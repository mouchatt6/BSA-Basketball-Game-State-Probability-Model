"""Compare ESPN and final MLP brier scores on a held-out test season.

Default setup mirrors mlp_final.ipynb:
  - train final MLP on 2021-22, 2022-23, 2023-24, and 2024-25
  - evaluate on 2025-26
  - compare against cached ESPN win probability for the same test games

ESPN data is read from data/espn_wp as *_espn_wp.csv. Missing ESPN files are not
fetched here; run pull_espn_wp_cache.py first to build/update the local cache.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from pull_win_probability import to_nba_game_id


PBP_PATH = Path("data/pbp_all.csv")
ESPN_DIR = Path("data/espn_wp")
OUTPUT_DIR = Path("data")
CHUNK_SIZE = 250_000

NUMERIC_FEATURES = [
    "periodSecondsLeft",
    "secondsLeft",
    "scoreDif",
    "scoreTimePressure",
    "pointsTotal",
    "possession",
    "homeFouls",
    "awayFouls",
    "homeBonus",
    "awayBonus",
    "homeFreeThrows",
    "awayFreeThrows",
    "homeEjections",
    "awayEjections",
    "line",
]
ONE_HOT_FEATURES = ["quarter"]
TARGET = "homeWin"
FEATURE_COLS = NUMERIC_FEATURES + ONE_HOT_FEATURES
META_COLS = [
    "season",
    "gameId",
    "gameDate",
    "matchup",
    "homeTeamId",
    "awayTeamId",
    "homeWin",
]


def add_score_time_pressure(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["scoreTimePressure"] = np.tanh(
        out["scoreDif"].to_numpy(dtype=np.float64)
        / (out["secondsLeft"].to_numpy(dtype=np.float64) + 1.0)
    )
    return out


def brier_score(y_true: Iterable[float], y_prob: Iterable[float]) -> float:
    y_true_arr = np.asarray(y_true, dtype=float)
    y_prob_arr = np.asarray(y_prob, dtype=float)
    return float(np.mean((y_prob_arr - y_true_arr) ** 2))


def _numeric_scale_stats(x_train: np.ndarray, n_numeric: int) -> tuple[np.ndarray, np.ndarray]:
    mean = x_train[:, :n_numeric].mean(axis=0)
    std = x_train[:, :n_numeric].std(axis=0)
    std[std == 0] = 1.0
    return mean.astype(np.float32), std.astype(np.float32)


class MLP(nn.Module):
    """MLP with train-set standardization on the first n_numeric columns."""

    def __init__(
        self,
        n_numeric: int,
        n_onehot: int,
        hidden_layers: list[int],
        output_dim: int = 1,
        num_mean: torch.Tensor | None = None,
        num_std: torch.Tensor | None = None,
    ) -> None:
        super().__init__()
        self.n_numeric = n_numeric
        self.n_onehot = n_onehot

        if num_mean is None:
            num_mean = torch.zeros(n_numeric)
        if num_std is None:
            num_std = torch.ones(n_numeric)
        self.register_buffer("num_mean", num_mean.float().view(1, -1))
        self.register_buffer("num_std", num_std.float().view(1, -1))

        input_dim = n_numeric + n_onehot
        dims = [input_dim] + list(hidden_layers) + [output_dim]
        layers: list[nn.Module] = []
        for i in range(len(dims) - 1):
            layers.append(nn.Linear(dims[i], dims[i + 1]))
            if i < len(dims) - 2:
                layers.append(nn.ReLU())
        self.net = nn.Sequential(*layers)

    @classmethod
    def from_train_matrix(
        cls, x_train: np.ndarray, hidden_layers: list[int], n_numeric: int
    ) -> MLP:
        mean, std = _numeric_scale_stats(x_train, n_numeric)
        n_onehot = x_train.shape[1] - n_numeric
        return cls(
            n_numeric,
            n_onehot,
            hidden_layers,
            num_mean=torch.tensor(mean),
            num_std=torch.tensor(std),
        )

    def _encode(self, x: torch.Tensor) -> torch.Tensor:
        num = (x[:, : self.n_numeric] - self.num_mean) / self.num_std
        if self.n_onehot == 0:
            return num
        return torch.cat([num, x[:, self.n_numeric :]], dim=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(self._encode(x))


@dataclass
class TrainedModel:
    feature_pipeline: Pipeline
    model: MLP
    feature_cols: list[str]

    @torch.no_grad()
    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        self.model.eval()
        x = self.feature_pipeline.transform(df[self.feature_cols]).astype(np.float32)
        logits = self.model(torch.tensor(x, dtype=torch.float32))
        return torch.sigmoid(logits).detach().cpu().numpy().reshape(-1)

    def save(self, prefix: str) -> None:
        joblib.dump(self.feature_pipeline, f"{prefix}_feature_pipeline.joblib")
        torch.save(
            {
                "state_dict": self.model.state_dict(),
                "hidden_layers": [8],
                "n_numeric": self.model.n_numeric,
                "n_onehot": self.model.n_onehot,
                "feature_cols": self.feature_cols,
            },
            f"{prefix}_mlp.pt",
        )


def load_model_data(
    pbp_path: Path,
    train_seasons: list[str],
    test_season: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    usecols = list(dict.fromkeys(META_COLS + FEATURE_COLS))
    available = set(pd.read_csv(pbp_path, nrows=0).columns)
    usecols = [col for col in usecols if col in available and col != "scoreTimePressure"]
    parts: list[pd.DataFrame] = []

    wanted_seasons = set(train_seasons + [test_season])
    for chunk in pd.read_csv(
        pbp_path,
        usecols=usecols,
        chunksize=CHUNK_SIZE,
        dtype={"gameId": str},
        low_memory=False,
    ):
        chunk = chunk.loc[chunk["season"].isin(wanted_seasons)].copy()
        if chunk.empty:
            continue
        chunk["gameId"] = chunk["gameId"].map(to_nba_game_id)
        parts.append(chunk)

    if not parts:
        raise ValueError(f"No rows for seasons {sorted(wanted_seasons)} in {pbp_path}")

    df = add_score_time_pressure(pd.concat(parts, ignore_index=True))
    train_df = df.loc[df["season"].isin(train_seasons)].copy()
    test_df = df.loc[df["season"] == test_season].copy()
    if train_df.empty or test_df.empty:
        raise ValueError(
            f"Empty train/test split. train={len(train_df):,}, test={len(test_df):,}"
        )
    return train_df, test_df


def drop_model_na(df: pd.DataFrame, split_name: str) -> pd.DataFrame:
    required = FEATURE_COLS + [TARGET]
    n = len(df)
    out = df.dropna(subset=required).copy()
    print(
        f"{split_name}: dropped {n - len(out):,} rows with NaN in model columns "
        f"({len(out):,} remaining)"
    )
    return out


def train_final_mlp(
    train_df: pd.DataFrame,
    *,
    hidden_layers: list[int],
    lr: float,
    weight_decay: float,
    batch_size: int,
    epochs: int,
    seed: int,
) -> TrainedModel:
    torch.manual_seed(seed)
    np.random.seed(seed)

    n_numeric = len(NUMERIC_FEATURES)
    preprocess = ColumnTransformer(
        transformers=[
            ("num", "passthrough", NUMERIC_FEATURES),
            (
                "oh",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                ONE_HOT_FEATURES,
            ),
        ],
    )
    feature_pipeline = Pipeline([("preprocess", preprocess)])
    feature_pipeline.fit(train_df[FEATURE_COLS])

    x_train = feature_pipeline.transform(train_df[FEATURE_COLS]).astype(np.float32)
    y_train = train_df[TARGET].to_numpy(dtype=np.float32)
    xtr = torch.tensor(x_train, dtype=torch.float32)
    ytr = torch.tensor(y_train, dtype=torch.float32).view(-1, 1)

    model = MLP.from_train_matrix(x_train, hidden_layers, n_numeric)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

    key = f"arch={hidden_layers},lr={lr},opt=AdamW,wd={weight_decay}"
    print(f"Training final MLP ({key}), batch_size={batch_size}, epochs={epochs}")
    for epoch in range(1, epochs + 1):
        model.train()
        perm = torch.randperm(xtr.size(0))
        epoch_loss = 0.0
        for i in range(0, xtr.size(0), batch_size):
            idx = perm[i : i + batch_size]
            bx, by = xtr[idx], ytr[idx]
            optimizer.zero_grad()
            loss = criterion(model(bx), by)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * bx.size(0)
        print(f"epoch {epoch}/{epochs} train={epoch_loss / xtr.size(0):.6f}")

    return TrainedModel(feature_pipeline, model, FEATURE_COLS)


def test_game_ids(test_df: pd.DataFrame) -> list[str]:
    return sorted(test_df["gameId"].dropna().map(to_nba_game_id).unique())


def ensure_espn_cache(
    test_df: pd.DataFrame, espn_dir: Path, *, allow_missing_espn: bool
) -> list[str]:
    ids = test_game_ids(test_df)
    missing = [gid for gid in ids if not (espn_dir / f"{gid}_espn_wp.csv").is_file()]
    print(f"ESPN cache: {len(ids) - len(missing):,}/{len(ids):,} test games present")
    if not missing:
        return ids
    if allow_missing_espn:
        preview = ", ".join(missing[:10])
        print(
            f"WARNING: excluding {len(missing):,} test games without cached ESPN WP: "
            f"{preview}"
        )
        return [gid for gid in ids if gid not in set(missing)]
    preview = ", ".join(missing[:5])
    raise FileNotFoundError(
        f"Missing {len(missing):,} ESPN files under {espn_dir}. "
        f"First missing: {preview}. Run: "
        f"python pull_espn_wp_cache.py --season {test_df['season'].iloc[0]}"
    )


def load_espn_for_games(game_ids: list[str], espn_dir: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for gid in game_ids:
        path = espn_dir / f"{gid}_espn_wp.csv"
        if not path.is_file():
            continue
        df = pd.read_csv(path)
        df["game_id"] = gid
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"No ESPN files for requested games under {espn_dir}")
    out = pd.concat(frames, ignore_index=True)
    out["espn_wp"] = pd.to_numeric(out["home_win_pct"], errors="coerce")
    return out.dropna(subset=["espn_wp"])


def attach_home_win(espn: pd.DataFrame, test_df: pd.DataFrame) -> pd.DataFrame:
    outcomes = (
        test_df[["gameId", "homeWin"]]
        .drop_duplicates("gameId")
        .assign(game_id=lambda d: d["gameId"].map(to_nba_game_id))
        .set_index("game_id")["homeWin"]
        .astype(float)
    )
    out = espn.copy()
    out["homeWin"] = out["game_id"].map(outcomes)
    missing = out["homeWin"].isna()
    if missing.any():
        raise ValueError(
            f"homeWin missing for {missing.sum():,} ESPN rows "
            f"({out.loc[missing, 'game_id'].nunique():,} games)"
        )
    return out


def summarize_comparison(
    test_df: pd.DataFrame,
    model: TrainedModel,
    espn: pd.DataFrame,
    output_path: Path,
) -> pd.DataFrame:
    comparison_ids = set(espn["game_id"].unique())
    excluded = sorted(set(test_df["gameId"].map(to_nba_game_id).unique()) - comparison_ids)
    if excluded:
        print(
            f"Excluding {len(excluded):,} model-test games without ESPN WP from "
            f"aggregate comparison: {', '.join(excluded[:10])}"
        )

    scored = test_df.loc[test_df["gameId"].map(to_nba_game_id).isin(comparison_ids)].copy()
    scored["model_wp"] = model.predict_proba(scored)

    model_by_game = (
        scored.assign(model_sq=(scored["model_wp"] - scored["homeWin"]) ** 2)
        .groupby("gameId", as_index=False)
        .agg(
            model_brier=("model_sq", "mean"),
            model_rows=("model_sq", "size"),
            matchup=("matchup", "first"),
        )
        .rename(columns={"gameId": "game_id"})
    )
    espn_by_game = (
        espn.assign(espn_sq=(espn["espn_wp"] - espn["homeWin"]) ** 2)
        .groupby("game_id", as_index=False)
        .agg(espn_brier=("espn_sq", "mean"), espn_rows=("espn_sq", "size"))
    )
    by_game = model_by_game.merge(espn_by_game, on="game_id", how="inner")
    by_game["model_minus_espn"] = by_game["model_brier"] - by_game["espn_brier"]
    by_game = by_game[
        [
            "game_id",
            "matchup",
            "model_brier",
            "espn_brier",
            "model_minus_espn",
            "model_rows",
            "espn_rows",
        ]
    ].sort_values("game_id")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    by_game.to_csv(output_path, index=False)

    print("\nTest-set brier comparison")
    print(f"Games compared: {by_game['game_id'].nunique():,}")
    print(
        f"MLP Brier (all model rows):       "
        f"{brier_score(scored['homeWin'], scored['model_wp']):.6f}"
    )
    print(
        f"ESPN Brier (all ESPN rows):       "
        f"{brier_score(espn['homeWin'], espn['espn_wp']):.6f}"
    )
    print(f"MLP Brier (mean per game):       {by_game['model_brier'].mean():.6f}")
    print(f"ESPN Brier (mean per game):      {by_game['espn_brier'].mean():.6f}")
    print(f"MLP - ESPN (mean per game):      {by_game['model_minus_espn'].mean():+.6f}")
    print(f"Wrote per-game comparison: {output_path}")
    return by_game


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train final MLP through 2024-25 and compare to ESPN on 2025-26."
    )
    parser.add_argument("--pbp-path", type=Path, default=PBP_PATH)
    parser.add_argument("--espn-dir", type=Path, default=ESPN_DIR)
    parser.add_argument("--test-season", default="2025-26")
    parser.add_argument(
        "--train-seasons",
        nargs="+",
        default=["2021-22", "2022-23", "2023-24", "2024-25"],
    )
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=2048)
    parser.add_argument("--lr", type=float, default=0.01)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--seed", type=int, default=10)
    parser.add_argument("--save-model-prefix", default=None)
    parser.add_argument(
        "--allow-missing-espn",
        action="store_true",
        help="Compare only games with cached ESPN WP instead of failing on missing files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR / "brier_by_game_2025_26.csv",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(f"Train seasons: {', '.join(args.train_seasons)}")
    print(f"Test season:   {args.test_season}")

    train_df, test_df = load_model_data(args.pbp_path, args.train_seasons, args.test_season)
    train_df = drop_model_na(train_df, "train")
    test_df = drop_model_na(test_df, "test")

    model = train_final_mlp(
        train_df,
        hidden_layers=[8],
        lr=args.lr,
        weight_decay=args.weight_decay,
        batch_size=args.batch_size,
        epochs=args.epochs,
        seed=args.seed,
    )
    if args.save_model_prefix:
        model.save(args.save_model_prefix)
        print(f"Saved model artifacts with prefix {args.save_model_prefix!r}")

    ids = ensure_espn_cache(
        test_df, args.espn_dir, allow_missing_espn=args.allow_missing_espn
    )
    espn = attach_home_win(load_espn_for_games(ids, args.espn_dir), test_df)
    summarize_comparison(test_df, model, espn, args.output)


if __name__ == "__main__":
    main()
