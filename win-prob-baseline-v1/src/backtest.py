from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from .baseline import BaselineModel, brier_score, fit_baseline_model, log_loss
    from .data_loader import load_betting_data, split_train_test
except ImportError:
    from baseline import BaselineModel, brier_score, fit_baseline_model, log_loss
    from data_loader import load_betting_data, split_train_test


@dataclass
class BacktestResult:
    game_predictions: pd.DataFrame
    rolling_metrics: pd.DataFrame
    summary: dict[str, float]


def _calibration_table(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    bins: int = 10,
) -> pd.DataFrame:
    df = pd.DataFrame({"y_true": y_true, "y_prob": y_prob})
    edges = np.linspace(0.0, 1.0, bins + 1)
    # include_lowest=True so p=0.0 falls in first bucket if ever present
    df["bucket"] = pd.cut(df["y_prob"], bins=edges, include_lowest=True)
    grouped = (
        df.groupby("bucket", observed=False)
        .agg(
            n=("y_true", "size"),
            mean_pred=("y_prob", "mean"),
            win_rate=("y_true", "mean"),
        )
        .reset_index()
    )
    grouped["calibration_gap_abs"] = (grouped["mean_pred"] - grouped["win_rate"]).abs()
    return grouped


def run_rolling_backtest(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    retrain_every_games: int = 50,
    rolling_window: int = 200,
) -> BacktestResult:
    history = train_df.copy().sort_values("date").reset_index(drop=True)
    test = test_df.copy().sort_values("date").reset_index(drop=True)

    if history.empty or test.empty:
        raise ValueError("Training and test sets must both be non-empty.")

    model = fit_baseline_model(history)
    pred_rows: list[dict] = []

    for idx, row in test.iterrows():
        if idx > 0 and idx % retrain_every_games == 0:
            model = fit_baseline_model(history)

        spread = float(row["signed_spread_home"])
        p_model = float(model.predict_proba(np.array([spread]))[0])
        p_normal = float(model.normal_cdf_rule(np.array([spread]))[0])

        pred_rows.append(
            {
                "date": row["date"],
                "season": int(row["season"]),
                "home": row["home"],
                "away": row["away"],
                "signed_spread_home": spread,
                "home_win": int(row["home_win"]),
                "pred_home_win_prob_model": p_model,
                "pred_home_win_prob_normal_rule": p_normal,
            }
        )

        history = pd.concat([history, test.iloc[[idx]]], ignore_index=True)

    preds = pd.DataFrame(pred_rows).sort_values("date").reset_index(drop=True)

    y = preds["home_win"].to_numpy(dtype=float)
    p = preds["pred_home_win_prob_model"].to_numpy(dtype=float)

    rolling_rows: list[dict] = []
    for i in range(1, len(preds) + 1):
        y_cum = y[:i]
        p_cum = p[:i]
        start = max(0, i - rolling_window)
        y_roll = y[start:i]
        p_roll = p[start:i]
        rolling_rows.append(
            {
                "date": preds.loc[i - 1, "date"],
                "games_seen": i,
                "cum_log_loss": log_loss(y_cum, p_cum),
                "cum_brier": brier_score(y_cum, p_cum),
                "rolling_log_loss": log_loss(y_roll, p_roll),
                "rolling_brier": brier_score(y_roll, p_roll),
            }
        )

    rolling = pd.DataFrame(rolling_rows)
    preds["correct_pick"] = (
        ((preds["pred_home_win_prob_model"] >= 0.5) & (preds["home_win"] == 1))
        | ((preds["pred_home_win_prob_model"] < 0.5) & (preds["home_win"] == 0))
    ).astype(int)
    high_conf = preds[(preds["pred_home_win_prob_model"] >= 0.6) | (preds["pred_home_win_prob_model"] <= 0.4)]
    high_conf_hit_rate = float(high_conf["correct_pick"].mean()) if len(high_conf) else float("nan")

    calibration = _calibration_table(y_true=y, y_prob=p, bins=10)
    summary = {
        "games": float(len(preds)),
        "log_loss": log_loss(y, p),
        "brier": brier_score(y, p),
        "accuracy_at_0_5": float(preds["correct_pick"].mean()),
        "high_confidence_hit_rate": high_conf_hit_rate,
        "high_confidence_games": float(len(high_conf)),
        "mean_abs_calibration_gap": float(calibration["calibration_gap_abs"].mean(skipna=True)),
    }

    return BacktestResult(game_predictions=preds, rolling_metrics=rolling, summary=summary)


def calibration_table_from_predictions(predictions: pd.DataFrame, bins: int = 10) -> pd.DataFrame:
    y = predictions["home_win"].to_numpy(dtype=float)
    p = predictions["pred_home_win_prob_model"].to_numpy(dtype=float)
    return _calibration_table(y_true=y, y_prob=p, bins=bins)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    repo_root = project_root.parent
    parser = argparse.ArgumentParser(description="Run rolling backtest of the baseline model.")
    parser.add_argument("--csv", type=Path, default=repo_root / "nba_2008-2025.csv")
    parser.add_argument("--train-season", type=int, default=2024)
    parser.add_argument("--test-season", type=int, default=2025)
    parser.add_argument("--retrain-every", type=int, default=50, help="Retrain cadence in test games")
    parser.add_argument("--rolling-window", type=int, default=200, help="Rolling-metric window size")
    parser.add_argument(
        "--outputs-dir",
        type=Path,
        default=project_root / "outputs",
        help="Directory to write backtest artifacts",
    )
    parser.add_argument("--calibration-bins", type=int, default=10)
    args = parser.parse_args()

    print(f"Loading {args.csv}...")
    data = load_betting_data(args.csv)
    train_df, test_df = split_train_test(
        data,
        train_season=args.train_season,
        test_season=args.test_season,
        regular_only=True,
    )

    print(f"Running rolling backtest: {len(test_df)} test games | "
          f"retrain every {args.retrain_every} | rolling window {args.rolling_window}")
    result = run_rolling_backtest(
        train_df=train_df,
        test_df=test_df,
        retrain_every_games=args.retrain_every,
        rolling_window=args.rolling_window,
    )

    args.outputs_dir.mkdir(parents=True, exist_ok=True)
    preds_path = args.outputs_dir / f"backtest_{args.test_season}_game_predictions.csv"
    rolling_path = args.outputs_dir / f"backtest_{args.test_season}_rolling_metrics.csv"
    summary_path = args.outputs_dir / f"backtest_{args.test_season}_summary.json"
    calibration_path = args.outputs_dir / f"backtest_{args.test_season}_calibration.csv"

    result.game_predictions.to_csv(preds_path, index=False)
    result.rolling_metrics.to_csv(rolling_path, index=False)
    summary_path.write_text(json.dumps(result.summary, indent=2))
    calibration_table_from_predictions(result.game_predictions, bins=args.calibration_bins).to_csv(
        calibration_path, index=False
    )

    print(f"Summary: {result.summary}")
    print(f"Wrote predictions      -> {preds_path}")
    print(f"Wrote rolling metrics  -> {rolling_path}")
    print(f"Wrote summary          -> {summary_path}")
    print(f"Wrote calibration      -> {calibration_path}")


if __name__ == "__main__":
    main()

