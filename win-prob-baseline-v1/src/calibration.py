from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
import time

import pandas as pd
import yaml
from nba_api.stats.endpoints import leaguegamefinder
from sklearn.cluster import KMeans
from sklearn.linear_model import Ridge

try:
    from .player_adjustment import PositionWeightConfig
except ImportError:
    from player_adjustment import PositionWeightConfig


@dataclass
class CalibratedWeights:
    default_position: str
    stat_coefficients: dict[str, float]
    position_multipliers: dict[str, dict[str, float]]
    raw_position_stat_coefficients: dict[str, dict[str, float]]
    training_rows: int

    def to_payload(self) -> dict:
        return asdict(self)

def _fetch_player_games(season: str, cache_path: Path) -> pd.DataFrame:
    if cache_path.exists():
        df = pd.read_csv(cache_path)
    else:
        last_err: Exception | None = None
        df = None
        for attempt in range(1, 4):
            try:
                finder = leaguegamefinder.LeagueGameFinder(
                    season_nullable=season,
                    season_type_nullable="Regular Season",
                    player_or_team_abbreviation="P",
                    league_id_nullable="00",
                    timeout=90,
                )
                df = finder.get_data_frames()[0].copy()
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(cache_path, index=False)
                break
            except Exception as exc:
                last_err = exc
                time.sleep(1.5 * attempt)
        if df is None:
            raise RuntimeError(f"Failed to fetch player game logs for season={season}") from last_err

    required = {"GAME_ID", "TEAM_ID", "PLAYER_ID", "MATCHUP", "PTS", "REB", "AST"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Player game logs missing expected columns: {sorted(missing)}")
    return df


def _infer_player_position_map(player_games: pd.DataFrame) -> dict[int, str]:
    df = player_games.copy()
    for col in ["PLAYER_ID", "MIN", "PTS", "REB", "AST"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["PLAYER_ID", "MIN", "PTS", "REB", "AST"]).copy()
    df["PLAYER_ID"] = df["PLAYER_ID"].astype(int)
    df = df[df["MIN"] >= 5].copy()

    player_profile = (
        df.groupby("PLAYER_ID", as_index=False)
        .agg(
            gp=("GAME_ID", "count"),
            mpg=("MIN", "mean"),
            pts=("PTS", "mean"),
            reb=("REB", "mean"),
            ast=("AST", "mean"),
        )
    )
    player_profile = player_profile[player_profile["gp"] >= 10].copy()
    if player_profile.empty:
        return {}

    feature_cols = ["pts", "reb", "ast"]
    X = player_profile[feature_cols].to_numpy(dtype=float)
    km = KMeans(n_clusters=3, random_state=42, n_init=20)
    player_profile["cluster"] = km.fit_predict(X)
    centers = pd.DataFrame(km.cluster_centers_, columns=feature_cols)
    centers["cluster"] = centers.index

    centers["guard_score"] = centers["ast"] - 0.35 * centers["reb"]
    guard_cluster = int(centers.sort_values("guard_score", ascending=False).iloc[0]["cluster"])

    remaining_for_center = centers[centers["cluster"] != guard_cluster].copy()
    remaining_for_center["center_score"] = remaining_for_center["reb"] - 0.35 * remaining_for_center["ast"]
    center_cluster = int(remaining_for_center.sort_values("center_score", ascending=False).iloc[0]["cluster"])

    forward_cluster = int(({0, 1, 2} - {guard_cluster, center_cluster}).pop())

    cluster_to_pos = {
        guard_cluster: "G",
        forward_cluster: "F",
        center_cluster: "C",
    }
    player_profile["position"] = player_profile["cluster"].map(cluster_to_pos).fillna("F")
    return dict(zip(player_profile["PLAYER_ID"], player_profile["position"]))


def _build_training_frame(player_games: pd.DataFrame, player_positions: dict[int, str]) -> pd.DataFrame:
    df = player_games.copy()
    df["PLAYER_ID"] = pd.to_numeric(df["PLAYER_ID"], errors="coerce")
    df["PTS"] = pd.to_numeric(df["PTS"], errors="coerce")
    df["REB"] = pd.to_numeric(df["REB"], errors="coerce")
    df["AST"] = pd.to_numeric(df["AST"], errors="coerce")
    df = df.dropna(subset=["PLAYER_ID", "PTS", "REB", "AST", "MATCHUP"]).copy()
    df["PLAYER_ID"] = df["PLAYER_ID"].astype(int)
    df["position"] = df["PLAYER_ID"].map(player_positions).fillna("F")
    df["is_home"] = df["MATCHUP"].astype(str).str.contains("vs.")
    df["side"] = df["is_home"].map({True: "home", False: "away"})

    agg = (
        df.groupby(["GAME_ID", "side", "position"], as_index=False)
        .agg(pts=("PTS", "sum"), reb=("REB", "sum"), ast=("AST", "sum"))
    )
    pivot = agg.pivot_table(
        index=["GAME_ID"],
        columns=["side", "position"],
        values=["pts", "reb", "ast"],
        fill_value=0.0,
    )
    pivot.columns = ["_".join(col) for col in pivot.columns.to_flat_index()]
    pivot = pivot.reset_index()

    for stat in ["pts", "reb", "ast"]:
        for pos in ["G", "F", "C"]:
            home_col = f"{stat}_home_{pos}"
            away_col = f"{stat}_away_{pos}"
            if home_col not in pivot.columns:
                pivot[home_col] = 0.0
            if away_col not in pivot.columns:
                pivot[away_col] = 0.0
            pivot[f"diff_{stat}_{pos}"] = pivot[home_col] - pivot[away_col]

    pivot["home_points"] = (
        pivot["pts_home_G"] + pivot["pts_home_F"] + pivot["pts_home_C"]
    )
    pivot["away_points"] = (
        pivot["pts_away_G"] + pivot["pts_away_F"] + pivot["pts_away_C"]
    )
    pivot["home_margin"] = pivot["home_points"] - pivot["away_points"]
    return pivot


def calibrate_position_weights(
    season: str = "2023-24",
    ridge_alpha: float = 10.0,
    cache_dir: Path | str | None = None,
) -> CalibratedWeights:
    cache_root = Path(cache_dir) if cache_dir else Path(__file__).resolve().parents[1] / "data"
    cache_file = cache_root / f"player_game_logs_{season}.csv"
    games = _fetch_player_games(season=season, cache_path=cache_file)
    player_pos = _infer_player_position_map(player_games=games)
    train = _build_training_frame(player_games=games, player_positions=player_pos)

    feature_cols = [
        "diff_pts_G",
        "diff_pts_F",
        "diff_pts_C",
        "diff_reb_G",
        "diff_reb_F",
        "diff_reb_C",
        "diff_ast_G",
        "diff_ast_F",
        "diff_ast_C",
    ]
    X = train[feature_cols].to_numpy(dtype=float)
    y = train["home_margin"].to_numpy(dtype=float)

    model = Ridge(alpha=ridge_alpha, fit_intercept=True, random_state=42)
    model.fit(X, y)

    coef_map = dict(zip(feature_cols, model.coef_))

    # F is anchor position for each stat.
    stat_coefficients = {
        "points": float(abs(coef_map["diff_pts_F"])),
        "rebounds": float(abs(coef_map["diff_reb_F"])),
        "assists": float(abs(coef_map["diff_ast_F"])),
    }
    for key, val in stat_coefficients.items():
        if val < 1e-6:
            raise ValueError(f"Calibrated base coefficient for {key} is near zero; cannot normalize.")

    position_multipliers = {
        "G": {
            "points": float(coef_map["diff_pts_G"] / coef_map["diff_pts_F"]),
            "rebounds": float(coef_map["diff_reb_G"] / coef_map["diff_reb_F"]),
            "assists": float(coef_map["diff_ast_G"] / coef_map["diff_ast_F"]),
        },
        "F": {"points": 1.0, "rebounds": 1.0, "assists": 1.0},
        "C": {
            "points": float(coef_map["diff_pts_C"] / coef_map["diff_pts_F"]),
            "rebounds": float(coef_map["diff_reb_C"] / coef_map["diff_reb_F"]),
            "assists": float(coef_map["diff_ast_C"] / coef_map["diff_ast_F"]),
        },
    }

    raw_position_stat = {
        "G": {
            "points": float(coef_map["diff_pts_G"]),
            "rebounds": float(coef_map["diff_reb_G"]),
            "assists": float(coef_map["diff_ast_G"]),
        },
        "F": {
            "points": float(coef_map["diff_pts_F"]),
            "rebounds": float(coef_map["diff_reb_F"]),
            "assists": float(coef_map["diff_ast_F"]),
        },
        "C": {
            "points": float(coef_map["diff_pts_C"]),
            "rebounds": float(coef_map["diff_reb_C"]),
            "assists": float(coef_map["diff_ast_C"]),
        },
    }

    return CalibratedWeights(
        default_position="F",
        stat_coefficients=stat_coefficients,
        position_multipliers=position_multipliers,
        raw_position_stat_coefficients=raw_position_stat,
        training_rows=int(len(train)),
    )


def write_calibrated_config(calibrated: CalibratedWeights, config_path: Path | str) -> PositionWeightConfig:
    payload = {
        "default_position": calibrated.default_position,
        "stat_coefficients": calibrated.stat_coefficients,
        "position_multipliers": calibrated.position_multipliers,
    }
    out = Path(config_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(payload, sort_keys=False))
    return PositionWeightConfig.from_yaml(out)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Calibrate position-weighted player margin coefficients.")
    parser.add_argument("--season", default="2023-24", help="NBA season string, e.g. 2023-24")
    parser.add_argument("--ridge-alpha", type=float, default=10.0, help="Ridge regression regularization strength")
    parser.add_argument(
        "--config-path",
        type=Path,
        default=project_root / "configs" / "position_weights.yaml",
        help="Where to write the calibrated position_weights YAML",
    )
    parser.add_argument(
        "--weights-json",
        type=Path,
        default=project_root / "outputs" / "position_stat_weights.json",
        help="Where to write the full calibrated weights payload as JSON",
    )
    args = parser.parse_args()

    print(f"Calibrating position weights from season={args.season} (ridge_alpha={args.ridge_alpha})...")
    calibrated = calibrate_position_weights(season=args.season, ridge_alpha=args.ridge_alpha)
    write_calibrated_config(calibrated=calibrated, config_path=args.config_path)

    args.weights_json.parent.mkdir(parents=True, exist_ok=True)
    args.weights_json.write_text(json.dumps(calibrated.to_payload(), indent=2))

    print(f"Trained on {calibrated.training_rows} game rows.")
    print(f"Stat coefficients: {calibrated.stat_coefficients}")
    print(f"Wrote position config -> {args.config_path}")
    print(f"Wrote weights payload -> {args.weights_json}")


if __name__ == "__main__":
    main()

