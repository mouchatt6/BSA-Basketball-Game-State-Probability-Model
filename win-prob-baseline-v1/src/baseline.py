from __future__ import annotations

from dataclasses import asdict, dataclass
from math import erf, sqrt
from pathlib import Path
import json

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression


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

