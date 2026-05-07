from __future__ import annotations

import argparse
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


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    repo_root = project_root.parent
    parser = argparse.ArgumentParser(description="Load and inspect betting data.")
    parser.add_argument("--csv", type=Path, default=repo_root / "nba_2008-2025.csv")
    parser.add_argument("--train-season", type=int, default=2024)
    parser.add_argument("--test-season", type=int, default=2025)
    parser.add_argument("--include-playoffs", action="store_true", help="Include non-regular-season games")
    args = parser.parse_args()

    print(f"Loading {args.csv}...")
    df = load_betting_data(args.csv)
    print(f"Loaded {len(df)} rows across {df['season'].nunique()} seasons "
          f"({int(df['season'].min())}-{int(df['season'].max())}).")

    train_df, test_df = split_train_test(
        df,
        train_season=args.train_season,
        test_season=args.test_season,
        regular_only=not args.include_playoffs,
    )
    print(f"Train ({args.train_season}): {len(train_df)} games | "
          f"home win rate = {train_df['home_win'].mean():.3f}")
    print(f"Test  ({args.test_season}): {len(test_df)} games | "
          f"home win rate = {test_df['home_win'].mean():.3f}")


if __name__ == "__main__":
    main()
