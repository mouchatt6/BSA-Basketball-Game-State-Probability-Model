"""Fetch and cache ESPN NBA win-probability files for a season.

This is intentionally separate from compare_espn_test_brier.py so ESPN data can
be pulled once and reused across repeated model-comparison runs.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd

from pull_win_probability import fetch_with_retries, to_nba_game_id


PBP_PATH = Path("data/pbp_all.csv")
ESPN_DIR = Path("data/espn_wp")
CHUNK_SIZE = 250_000
META_COLS = ["season", "gameId", "gameDate", "matchup", "homeTeamId", "awayTeamId"]


def load_game_metadata(pbp_path: Path, season: str) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(
        pbp_path,
        usecols=META_COLS,
        chunksize=CHUNK_SIZE,
        dtype={"gameId": str},
        low_memory=False,
    ):
        sub = chunk.loc[chunk["season"] == season].copy()
        if sub.empty:
            continue
        sub["gameId"] = sub["gameId"].map(to_nba_game_id)
        parts.append(sub.drop_duplicates("gameId"))
    if not parts:
        raise ValueError(f"No games for season {season!r} in {pbp_path}")
    return pd.concat(parts, ignore_index=True).drop_duplicates("gameId")


def valid_cached_wp(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        df = pd.read_csv(path, nrows=1)
    except Exception:
        return False
    return "home_win_pct" in df.columns and not df.empty


def save_game_atomic(win_prob: pd.DataFrame, nba_game_id: str, out_dir: Path) -> Path:
    gid = to_nba_game_id(nba_game_id)
    path = out_dir / f"{gid}_espn_wp.csv"
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    win_prob.to_csv(tmp_path, index=False)
    tmp_path.replace(path)
    return path


def pull_espn_cache(
    games: pd.DataFrame,
    out_dir: Path,
    *,
    limit: int | None,
    sleep_sec: float,
    overwrite: bool,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    skipped: list[str] = []
    failures: list[dict[str, str]] = []

    games = games.sort_values("gameId")
    if limit is not None:
        games = games.head(limit)

    total = len(games)
    for i, (_, game_row) in enumerate(games.iterrows(), start=1):
        gid = to_nba_game_id(game_row["gameId"])
        path = out_dir / f"{gid}_espn_wp.csv"
        if valid_cached_wp(path) and not overwrite:
            skipped.append(gid)
            if i == 1 or i % 50 == 0 or i == total:
                print(f"[{i}/{total}] {gid} cached; skipped")
            continue
        if path.exists() and not overwrite:
            print(f"[{i}/{total}] {gid} has invalid cache; refetching")

        print(f"[{i}/{total}] fetching ESPN WP for {gid} ...", end=" ", flush=True)
        try:
            game = pd.DataFrame([game_row])
            wp = fetch_with_retries(game=game)
            path = save_game_atomic(wp, gid, out_dir)
            saved.append(gid)
            print(f"saved {len(wp):,} rows -> {path}")
        except Exception as exc:
            failures.append({"game_id": gid, "error": repr(exc)})
            print(f"FAILED: {exc}")
        time.sleep(sleep_sec)

    print(
        f"\nDone. saved={len(saved):,}, skipped={len(skipped):,}, "
        f"failed={len(failures):,}, out_dir={out_dir}"
    )
    if failures:
        failure_path = out_dir / f"failures_{int(time.time())}.csv"
        pd.DataFrame(failures).to_csv(failure_path, index=False)
        raise SystemExit(f"Wrote ESPN fetch failures to {failure_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cache ESPN win-probability CSVs for a season."
    )
    parser.add_argument("--season", default="2025-26")
    parser.add_argument("--pbp-path", type=Path, default=PBP_PATH)
    parser.add_argument("--out-dir", type=Path, default=ESPN_DIR)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sleep-sec", type=float, default=0.2)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    games = load_game_metadata(args.pbp_path, args.season)
    print(f"Found {len(games):,} games for {args.season} in {args.pbp_path}")
    pull_espn_cache(
        games,
        args.out_dir,
        limit=args.limit,
        sleep_sec=args.sleep_sec,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()
