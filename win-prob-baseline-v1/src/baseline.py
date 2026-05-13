from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from math import erf, sqrt
from pathlib import Path
import json

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

try:
    from .data_loader import load_betting_data, split_train_test
except ImportError:
    from data_loader import load_betting_data, split_train_test


@dataclass
class BaselineModel:
    intercept: float
    spread_coef: float
    sigma: float = 12.0

    def predict_proba(self, signed_spread_home: np.ndarray) -> np.ndarray:
        x = np.asarray(signed_spread_home, dtype=float)
        logits = self.intercept + self.spread_coef * x
        probs = 1.0 / (1.0 + np.exp(-logits))
        return np.clip(probs, 1e-6, 1 - 1e-6)

    def normal_cdf_rule(self, signed_spread_home: np.ndarray) -> np.ndarray:
        x = np.asarray(signed_spread_home, dtype=float) / self.sigma
        probs = 0.5 * (1.0 + np.vectorize(erf)(x / sqrt(2.0)))
        return np.clip(probs, 1e-6, 1 - 1e-6)

    def save(self, path: Path | str) -> None:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(asdict(self), indent=2))

    @staticmethod
    def load(path: Path | str) -> "BaselineModel":
        obj = json.loads(Path(path).read_text())
        return BaselineModel(**obj)


def fit_baseline_model(train_df: pd.DataFrame) -> BaselineModel:
    required = {"signed_spread_home", "home_win"}
    missing = required.difference(train_df.columns)
    if missing:
        raise ValueError(f"Missing required columns for baseline fit: {sorted(missing)}")

    fit_df = train_df[["signed_spread_home", "home_win"]].copy()
    fit_df["signed_spread_home"] = pd.to_numeric(fit_df["signed_spread_home"], errors="coerce")
    fit_df["home_win"] = pd.to_numeric(fit_df["home_win"], errors="coerce")
    fit_df = fit_df.dropna().copy()
    fit_df["home_win"] = fit_df["home_win"].astype(int)

    X = fit_df[["signed_spread_home"]].to_numpy()
    y = fit_df["home_win"].to_numpy()

    clf = LogisticRegression(max_iter=2000, random_state=42)
    clf.fit(X, y)

    return BaselineModel(
        intercept=float(clf.intercept_[0]),
        spread_coef=float(clf.coef_[0][0]),
        sigma=12.0,
    )


def log_loss(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    p = np.clip(np.asarray(y_prob, dtype=float), 1e-6, 1.0 - 1e-6)
    y = np.asarray(y_true, dtype=float)
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())


def brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_prob, dtype=float)
    return float(np.mean((p - y) ** 2))


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    repo_root = project_root.parent
    parser = argparse.ArgumentParser(description="Fit baseline win probability model.")
    parser.add_argument("--csv", type=Path, default=repo_root / "nba_2008-2025.csv")
    parser.add_argument("--train-season", type=int, default=2024)
    parser.add_argument("--test-season", type=int, default=2025)
    parser.add_argument(
        "--out",
        type=Path,
        default=project_root / "outputs" / "baseline_params.json",
        help="Where to write the model parameters as JSON",
    )
    args = parser.parse_args()

    print(f"Loading {args.csv}...")
    data = load_betting_data(args.csv)
    train_df, test_df = split_train_test(
        data,
        train_season=args.train_season,
        test_season=args.test_season,
        regular_only=True,
    )

    print(f"Fitting baseline model on {len(train_df)} train games...")
    model = fit_baseline_model(train_df)

    train_probs = model.predict_proba(train_df["signed_spread_home"].to_numpy())
    test_probs = model.predict_proba(test_df["signed_spread_home"].to_numpy())
    train_metrics = {
        "log_loss": log_loss(train_df["home_win"].to_numpy(), train_probs),
        "brier": brier_score(train_df["home_win"].to_numpy(), train_probs),
    }
    test_metrics = {
        "log_loss": log_loss(test_df["home_win"].to_numpy(), test_probs),
        "brier": brier_score(test_df["home_win"].to_numpy(), test_probs),
    }

    model.save(args.out)

    print(f"Intercept: {model.intercept:.4f} | spread_coef: {model.spread_coef:.4f}")
    print(f"Train metrics: log_loss={train_metrics['log_loss']:.4f}, brier={train_metrics['brier']:.4f}")
    print(f"Test  metrics: log_loss={test_metrics['log_loss']:.4f}, brier={test_metrics['brier']:.4f}")
    print(f"Wrote model params -> {args.out}")


if __name__ == "__main__":
    main()

