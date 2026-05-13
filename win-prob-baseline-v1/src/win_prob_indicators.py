from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .player_adjustment import (
    AssistDelta,
    PositionWeightConfig,
    ReboundDelta,
)

Stat = Literal["PTS", "REB", "AST"]

# F bucket is the anchor position used in the calibrated weights.
_ANCHOR_POSITION = "F"


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z))


@dataclass
class WinProbModel:
    """Likelihood indicators for the player sliders.

    Chains three derivatives:  player stat -> team margin -> win probability.

    `c[stat]` is the per-unit margin contribution at the anchor position;
    `w_pos` is the player's positional multiplier relative to that anchor.
    Caller multiplies them in the helpers below — kept separate so the same
    `WinProbModel` can serve multiple players with different positions.
    """

    alpha: float                       # logistic intercept (from baseline.py)
    beta_spread: float                 # logistic spread coefficient

    # stat-to-margin coefficients (anchor-position values).
    c: dict[Stat, float] = field(default_factory=dict)

    # Per-position multipliers relative to the anchor; populated by builders
    # so positional sensitivity can be queried without re-deriving the math.
    w_pos_by_position: dict[str, dict[Stat, float]] = field(default_factory=dict)

    def p_win(self, M_adj: float) -> float:
        return sigmoid(self.alpha + self.beta_spread * M_adj)

    # ------- The three indicators ------- #

    def slider_sensitivity(self,
                           p_win: float,
                           stat: Stat,
                           w_pos: float) -> float:
        """dp_win / dx_{p,s}  --  drives the green/red UI delta."""
        return p_win * (1.0 - p_win) * self.beta_spread * self.c[stat] * w_pos

    def slider_score(self,
                     y: int,
                     p_win: float,
                     stat: Stat,
                     w_pos: float) -> float:
        """dl/dx_{p,s}  --  used for fitting / calibration."""
        return (y - p_win) * self.beta_spread * self.c[stat] * w_pos

    def slider_fisher(self,
                      p_win: float,
                      stat: Stat,
                      w_pos: float) -> float:
        """Fisher information at the current slider value."""
        deriv = self.beta_spread * self.c[stat] * w_pos
        return p_win * (1.0 - p_win) * deriv * deriv

    # ------- Discrete slider move (exact, not linearized) ------- #

    def exact_winprob_delta(self,
                            M_adj_before: float,
                            delta_M: float) -> float:
        p_before = self.p_win(M_adj_before)
        p_after  = self.p_win(M_adj_before + delta_M)
        return p_after - p_before

    # ------- Convenience: position-aware indicators ------- #

    def position_weight(self, stat: Stat, position: str) -> float:
        bucket = self.w_pos_by_position.get(position)
        if bucket is None:
            bucket = self.w_pos_by_position.get(_ANCHOR_POSITION, {})
        return float(bucket.get(stat, 1.0))

    def sensitivity_for_player(self, p_win: float, stat: Stat, position: str) -> float:
        return self.slider_sensitivity(p_win, stat, self.position_weight(stat, position))

    def score_for_player(self, y: int, p_win: float, stat: Stat, position: str) -> float:
        return self.slider_score(y, p_win, stat, self.position_weight(stat, position))

    def fisher_for_player(self, p_win: float, stat: Stat, position: str) -> float:
        return self.slider_fisher(p_win, stat, self.position_weight(stat, position))


def _build_position_weights(position_config: PositionWeightConfig,
                            positions: list[str]) -> dict[str, dict[Stat, float]]:
    """Pre-compute the (c[stat], w_pos) decomposition for each position.

    PTS uses the existing ridge-derived multipliers; REB derives w_pos from
    the rebound calibration relative to F; AST is position-independent.
    """
    anchor_reb = ReboundDelta(1.0, _ANCHOR_POSITION).margin_contribution()

    out: dict[str, dict[Stat, float]] = {}
    for pos in positions:
        pts_mult = position_config.position_multipliers.get(
            pos, position_config.position_multipliers[position_config.default_position]
        ).get("points", 1.0)
        reb_w = ReboundDelta(1.0, pos).margin_contribution() / anchor_reb if anchor_reb else 1.0
        out[pos] = {"PTS": float(pts_mult), "REB": float(reb_w), "AST": 1.0}
    return out


def build_winprob_model(baseline_params: dict,
                        position_config: PositionWeightConfig,
                        positions: tuple[str, ...] = ("G", "F", "C")) -> WinProbModel:
    """Construct a `WinProbModel` from the artifacts run_v1 already produces."""
    c: dict[Stat, float] = {
        "PTS": float(position_config.stat_coefficients["points"]),
        "REB": float(ReboundDelta(1.0, _ANCHOR_POSITION).margin_contribution()),
        "AST": float(AssistDelta(1.0).margin_contribution()),
    }
    w_pos = _build_position_weights(position_config, list(positions))
    return WinProbModel(
        alpha=float(baseline_params["intercept"]),
        beta_spread=float(baseline_params["spread_coef"]),
        c=c,
        w_pos_by_position=w_pos,
    )


def load_winprob_model(outputs_dir: Path | str,
                       config_path: Path | str) -> WinProbModel:
    """Convenience loader for downstream tooling (notebooks, dashboards)."""
    baseline = json.loads(Path(outputs_dir).joinpath("baseline_params.json").read_text())
    cfg = PositionWeightConfig.from_yaml(config_path)
    return build_winprob_model(baseline, cfg)


def indicators_summary(model: WinProbModel,
                       p_wins: tuple[float, ...] = (0.5, 0.7, 0.9),
                       positions: tuple[str, ...] = ("G", "F", "C"),
                       stats: tuple[Stat, ...] = ("PTS", "REB", "AST")) -> list[dict]:
    """Tabulate sensitivity / score (y=1) / Fisher across canonical states."""
    rows: list[dict] = []
    for p in p_wins:
        for pos in positions:
            for stat in stats:
                w = model.position_weight(stat, pos)
                rows.append({
                    "p_win": float(p),
                    "position": pos,
                    "stat": stat,
                    "c_anchor": float(model.c[stat]),
                    "w_pos": float(w),
                    "margin_per_unit": float(model.c[stat] * w),
                    "sensitivity": float(model.slider_sensitivity(p, stat, w)),
                    "score_y_eq_1": float(model.slider_score(1, p, stat, w)),
                    "fisher": float(model.slider_fisher(p, stat, w)),
                })
    return rows
