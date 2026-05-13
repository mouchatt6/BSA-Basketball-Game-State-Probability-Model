from __future__ import annotations

import json
from dataclasses import asdict
from math import erf, sqrt
from pathlib import Path

import pandas as pd

from src.backtest import calibration_table_from_predictions, run_rolling_backtest
from src.baseline import brier_score, fit_baseline_model, log_loss
from src.calibration import calibrate_position_weights, write_calibrated_config
from src.data_loader import load_betting_data, split_train_test
from src.player_adjustment import (
    PlayerDelta,
    PositionWeightConfig,
    assist_calibration_payload,
    compute_player_margin_delta,
    rebound_calibration_payload,
)
from src.win_prob_indicators import build_winprob_model, indicators_summary


def _build_scenario_examples(config: PositionWeightConfig) -> pd.DataFrame:
    base_spread_home = 3.5
    sigma = 12.0

    scenarios = {
        "home_star_guard_plus": [
            PlayerDelta(
                player_id="home_g1",
                team_side="home",
                position="G",
                points_delta=5.0,
                rebounds_delta=1.0,
                assists_delta=2.0,
            )
        ],
        "away_center_dominant": [
            PlayerDelta(
                player_id="away_c1",
                team_side="away",
                position="C",
                points_delta=4.0,
                rebounds_delta=4.0,
                assists_delta=0.0,
            )
        ],
        "balanced_home_plus_away_minus": [
            PlayerDelta("home_g2", "home", "G", 3.0, 0.0, 2.0),
            PlayerDelta("home_f1", "home", "F", 2.0, 2.0, 1.0),
            PlayerDelta("away_g1", "away", "G", -2.0, 0.0, -1.0),
        ],
    }

    rows = []
    for name, players in scenarios.items():
        delta_margin = compute_player_margin_delta(players, config)
        z = (base_spread_home + delta_margin) / sigma
        # Normal-CDF probability using erf approximation.
        prob = 0.5 * (1.0 + erf(z / sqrt(2.0)))
        rows.append(
            {
                "scenario_name": name,
                "base_spread_home": base_spread_home,
                "delta_margin_from_players": delta_margin,
                "effective_spread_home": base_spread_home + delta_margin,
                "home_win_probability_normal_rule": float(prob),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    root = Path(__file__).resolve().parent
    csv_path = root.parent / "nba_2008-2025.csv"
    outputs_dir = root / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    data = load_betting_data(csv_path)
    train_df, test_df = split_train_test(data, train_season=2024, test_season=2025, regular_only=True)

    baseline = fit_baseline_model(train_df)
    train_probs = baseline.predict_proba(train_df["signed_spread_home"].to_numpy())
    train_metrics = {
        "train_games": float(len(train_df)),
        "train_log_loss": log_loss(train_df["home_win"].to_numpy(), train_probs),
        "train_brier": brier_score(train_df["home_win"].to_numpy(), train_probs),
    }

    baseline_payload = asdict(baseline) | train_metrics
    (outputs_dir / "baseline_params.json").write_text(json.dumps(baseline_payload, indent=2))

    backtest = run_rolling_backtest(train_df=train_df, test_df=test_df, retrain_every_games=50, rolling_window=200)
    backtest.game_predictions.to_csv(outputs_dir / "backtest_2025_game_predictions.csv", index=False)
    backtest.rolling_metrics.to_csv(outputs_dir / "backtest_2025_rolling_metrics.csv", index=False)
    (outputs_dir / "backtest_2025_summary.json").write_text(json.dumps(backtest.summary, indent=2))

    calibration = calibration_table_from_predictions(backtest.game_predictions, bins=10)
    calibration.to_csv(outputs_dir / "backtest_2025_calibration.csv", index=False)

    config_path = root / "configs" / "position_weights.yaml"
    calibrated = calibrate_position_weights(season="2023-24", ridge_alpha=10.0)
    position_config = write_calibrated_config(calibrated=calibrated, config_path=config_path)
    position_payload = calibrated.to_payload()
    (outputs_dir / "position_stat_weights.json").write_text(json.dumps(position_payload, indent=2))

    scenario_df = _build_scenario_examples(position_config)
    scenario_df.to_csv(outputs_dir / "player_slider_scenario_checks.csv", index=False)

    (outputs_dir / "rebound_calibration.json").write_text(
        json.dumps(rebound_calibration_payload(), indent=2)
    )
    (outputs_dir / "assist_calibration.json").write_text(
        json.dumps(assist_calibration_payload(), indent=2)
    )

    winprob_model = build_winprob_model(baseline_payload, position_config)
    indicators = indicators_summary(winprob_model)
    pd.DataFrame(indicators).to_csv(outputs_dir / "win_prob_indicators_summary.csv", index=False)

    print("Completed Baseline Win Probability V1 run.")
    print(f"Saved outputs in: {outputs_dir}")


if __name__ == "__main__":
    main()
