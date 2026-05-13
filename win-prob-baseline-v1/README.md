# Baseline Win Probability V1

Standalone first-pass model for NBA win probability with:

1. **Baseline game probability** from spread -> home-win probability (trained on 2024).
2. **Player slider adjustment** via position-weighted deltas for points/rebounds/assists.
3. **Rolling backtests** on 2025 regular season games.

## Data Source

- Uses repository file: `../nba_2008-2025.csv`
- Requires columns:
  - `season`, `date`, `regular`, `home`, `away`
  - `score_home`, `score_away`
  - `whos_favored`, `spread`

## Folder Layout

- `configs/position_weights.yaml`: V1 position multipliers + stat coefficients.
- `src/data_loader.py`: strict CSV loading and train/test split.
- `src/baseline.py`: logistic baseline model and core metrics.
- `src/calibration.py`: true calibration of position/stat weights from 2023-24 player game logs.
- `src/player_adjustment.py`: player delta -> margin adjustment.
- `src/backtest.py`: chronological rolling 2025 evaluation.
- `run_v1.py`: first-run entrypoint that trains and writes artifacts.
- `outputs/`: generated artifacts.

## Run

From repo root:

```bash
".venv/bin/python" "win-prob-baseline-v1/run_v1.py"
```

### Interactive Slider (one matchup test)

Run:

```bash
".venv/bin/python" "win-prob-baseline-v1/tools/matchup_slider_tk.py"
```

What it does:
- loads 2025 regular-season matchups from `nba_2008-2025.csv`,
- pulls actual players for the selected game (top 5 by minutes per team when available),
- shows an adjusted home-win probability meter at the top,
- lets you change those players with `PTS/REB/AST` sliders,
- recomputes adjusted probability live and compares against actual game result.

## First-Run Artifacts

- `outputs/baseline_params.json`
  - logistic intercept and spread coefficient
  - training diagnostics on 2024
- `outputs/position_stat_weights.json`
  - learned position/stat coefficients and multipliers used by slider layer
- `outputs/backtest_2025_game_predictions.csv`
  - per-game predictions for 2025
- `outputs/backtest_2025_rolling_metrics.csv`
  - cumulative and rolling log loss/Brier over 2025 timeline
- `outputs/backtest_2025_calibration.csv`
  - decile calibration table
- `outputs/backtest_2025_summary.json`
  - headline metrics for the 2025 run
- `outputs/player_slider_scenario_checks.csv`
  - controlled examples showing slider-driven margin and probability changes

## Assumptions (V1)

- Home-team win probability is modeled directly.
- Spread sign is normalized to home perspective:
  - favored home -> positive spread,
  - favored away -> negative spread.
- Player layer is scenario-based (counterfactual at inference time), but the weights are learned from historical player game logs.
- Position effects are calibrated from 2023-24 NBA regular season logs via ridge regression on home margin.

## Known Caveats / Open Flags

- **Assist–points double counting.** `compute_player_margin_delta` adds `AssistDelta.margin_contribution()` (~2.65 margin pts per assist, of which ~2.45 is `expected_pts_per_assist()`) on top of the points slider's contribution. In reality, the points produced by an assist also show up in the team's points scored — so moving both the PTS and AST sliders on the same player partially double-counts the assisted bucket. The `redistribute_assist_points()` helper in `src/player_adjustment.py` is the primitive for fixing this: subtract the passer's `direct_team_points()` from the team's own points contribution and credit only the `BETA_AST_PREMIUM` playmaking bump, distributing the assisted points to teammates by scoring share. Worth resolving before V2 / before any user-facing claims based on slider deltas.

## Next Up

- Replace fixed position multipliers with estimated player-specific coefficients.
- Add richer uncertainty model for player outcomes (distributional sliders).
- Add Monte Carlo possession/game simulation layer once coefficients stabilize.
