from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {
    "season",
    "date",
    "regular",
    "away",
    "home",
    "score_away",
    "score_home",
    "whos_favored",
    "spread",
}


def _coerce_regular_flag(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    as_text = series.astype(str).str.strip().str.lower()
    return as_text.isin({"true", "1", "t", "yes"})


def load_betting_data(csv_path: Path | str) -> pd.DataFrame:
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in betting data: {sorted(missing)}")

    clean = df.copy()
    clean["season"] = pd.to_numeric(clean["season"], errors="coerce").astype("Int64")
    clean["date"] = pd.to_datetime(clean["date"], errors="coerce")
    clean["regular"] = _coerce_regular_flag(clean["regular"])
    clean["spread"] = pd.to_numeric(clean["spread"], errors="coerce")
    clean["score_home"] = pd.to_numeric(clean["score_home"], errors="coerce")
    clean["score_away"] = pd.to_numeric(clean["score_away"], errors="coerce")
    clean["whos_favored"] = clean["whos_favored"].astype(str).str.strip().str.lower()

    clean = clean[
        clean["season"].notna()
        & clean["date"].notna()
        & clean["spread"].notna()
        & clean["score_home"].notna()
        & clean["score_away"].notna()
        & clean["whos_favored"].isin({"home", "away"})
    ].copy()

    clean["home_win"] = (clean["score_home"] > clean["score_away"]).astype(int)
    # Positive means expectation favors home team.
    clean["signed_spread_home"] = clean["spread"].where(clean["whos_favored"] == "home", -clean["spread"])

    clean = clean.sort_values(["date", "home", "away"]).reset_index(drop=True)
    return clean


def split_train_test(
    df: pd.DataFrame,
    train_season: int = 2024,
    test_season: int = 2025,
    regular_only: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = df.copy()
    if regular_only:
        frame = frame[frame["regular"]].copy()

    train_df = frame[frame["season"] == train_season].copy()
    test_df = frame[frame["season"] == test_season].copy()
    if train_df.empty:
        raise ValueError(f"No rows found for train_season={train_season}")
    if test_df.empty:
        raise ValueError(f"No rows found for test_season={test_season}")
    return train_df, test_df
