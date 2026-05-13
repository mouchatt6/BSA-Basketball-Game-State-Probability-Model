from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

TeamSide = Literal["home", "away"]


# ── Rebound impact calibration ────────────────────────────────────────────
# Calibrated from 2023-24 logs; override via YAML when retraining.
PI_O_BY_POS = {"PG": 0.18, "SG": 0.20, "SF": 0.22, "PF": 0.28, "C": 0.32}
# Bucket averages for the G/F/C system used elsewhere in this codebase.
PI_O_BY_BUCKET = {
    "G": (PI_O_BY_POS["PG"] + PI_O_BY_POS["SG"]) / 2,
    "F": (PI_O_BY_POS["SF"] + PI_O_BY_POS["PF"]) / 2,
    "C": PI_O_BY_POS["C"],
}
BETA_OREB = 1.10   # second-chance pts per OREB
BETA_DREB = 1.10   # pts denied per DREB-of-opp-OREB
RHO_D     = 0.30   # share of player DREB that is net-new vs. teammate reallocation


def _resolve_pi_o(position: str) -> float:
    if position in PI_O_BY_POS:
        return PI_O_BY_POS[position]
    if position in PI_O_BY_BUCKET:
        return PI_O_BY_BUCKET[position]
    return 0.24


@dataclass
class ReboundDelta:
    delta_reb: float
    position: str

    def margin_contribution(self) -> float:
        pi_o = _resolve_pi_o(self.position)
        pi_d = 1.0 - pi_o
        d_oreb = pi_o * self.delta_reb
        d_dreb = pi_d * self.delta_reb
        return BETA_OREB * d_oreb + BETA_DREB * RHO_D * d_dreb


def reb_winprob_delta(p_win: float,
                      beta_spread: float,
                      delta_reb: float,
                      position: str) -> float:
    """Linearized win-prob delta from a single player's REB slider change."""
    dM = ReboundDelta(delta_reb, position).margin_contribution()
    return p_win * (1.0 - p_win) * beta_spread * dM


def rebound_calibration_payload() -> dict:
    """Snapshot of the rebound-impact constants — used by run_v1 / dashboards."""
    return {
        "pi_o_by_position": dict(PI_O_BY_POS),
        "pi_o_by_bucket": {k: float(v) for k, v in PI_O_BY_BUCKET.items()},
        "beta_oreb": float(BETA_OREB),
        "beta_dreb": float(BETA_DREB),
        "rho_d": float(RHO_D),
    }


# ── Assist impact calibration ─────────────────────────────────────────────
PI_2          = 0.58
PI_3          = 0.42
PI_FT_GIVEN_2 = 0.06
PI_FT_GIVEN_3 = 0.02
PI_FT_MADE    = 0.78
BETA_AST_PREMIUM = 0.20   # marginal eFG bump from playmaking; set to 0 to disable


def assist_outcome_distribution() -> dict[str, dict[str, float]]:
    """Return P(Y) and E[Pts|Y] for the four assist outcomes."""
    p = {
        "2P":    PI_2 * (1 - PI_FT_GIVEN_2),
        "2P+FT": PI_2 * PI_FT_GIVEN_2,
        "3P":    PI_3 * (1 - PI_FT_GIVEN_3),
        "3P+FT": PI_3 * PI_FT_GIVEN_3,
    }
    e_pts = {
        "2P":    2.0,
        "2P+FT": 2.0 + PI_FT_MADE,
        "3P":    3.0,
        "3P+FT": 3.0 + PI_FT_MADE,
    }
    return {"p": p, "e_pts": e_pts}


def expected_pts_per_assist() -> float:
    d = assist_outcome_distribution()
    return sum(d["p"][y] * d["e_pts"][y] for y in d["p"])


@dataclass
class AssistDelta:
    delta_ast: float

    def direct_team_points(self) -> float:
        return self.delta_ast * expected_pts_per_assist()

    def margin_contribution(self) -> float:
        return self.direct_team_points() + BETA_AST_PREMIUM * self.delta_ast


def redistribute_assist_points(scoring_vec: dict[str, float],
                               passer: str,
                               delta_ast: float) -> dict[str, float]:
    """Allocate assisted points to teammates by current scoring share."""
    total_other = sum(s for name, s in scoring_vec.items() if name != passer)
    if total_other == 0:
        return {name: 0.0 for name in scoring_vec}
    pts_to_distribute = delta_ast * expected_pts_per_assist()
    return {
        name: (pts_to_distribute * s / total_other) if name != passer else 0.0
        for name, s in scoring_vec.items()
    }


def ast_winprob_delta(p_win: float,
                      beta_spread: float,
                      delta_ast: float) -> float:
    """Linearized win-prob delta from a single player's AST slider change."""
    dM = AssistDelta(delta_ast).margin_contribution()
    return p_win * (1.0 - p_win) * beta_spread * dM


def assist_calibration_payload() -> dict:
    """Snapshot of the assist-impact constants — used by run_v1 / dashboards."""
    return {
        "pi_2": float(PI_2),
        "pi_3": float(PI_3),
        "pi_ft_given_2": float(PI_FT_GIVEN_2),
        "pi_ft_given_3": float(PI_FT_GIVEN_3),
        "pi_ft_made": float(PI_FT_MADE),
        "beta_ast_premium": float(BETA_AST_PREMIUM),
        "expected_pts_per_assist": float(expected_pts_per_assist()),
        "outcome_distribution": assist_outcome_distribution(),
    }


@dataclass
class PlayerDelta:
    player_id: str
    team_side: TeamSide
    position: str
    points_delta: float
    rebounds_delta: float
    assists_delta: float


@dataclass
class PositionWeightConfig:
    default_position: str
    stat_coefficients: dict[str, float]
    position_multipliers: dict[str, dict[str, float]]

    @staticmethod
    def from_yaml(path: Path | str) -> "PositionWeightConfig":
        payload = yaml.safe_load(Path(path).read_text())
        return PositionWeightConfig(
            default_position=str(payload["default_position"]),
            stat_coefficients={k: float(v) for k, v in payload["stat_coefficients"].items()},
            position_multipliers={
                pos: {k: float(v) for k, v in stat_map.items()}
                for pos, stat_map in payload["position_multipliers"].items()
            },
        )


def _effective_multiplier(config: PositionWeightConfig, position: str, stat_name: str) -> float:
    pos = position if position in config.position_multipliers else config.default_position
    pos_map = config.position_multipliers[pos]
    return float(pos_map.get(stat_name, 1.0))


def compute_player_margin_delta(players: list[PlayerDelta], config: PositionWeightConfig) -> float:
    total = 0.0
    for player in players:
        sign = 1.0 if player.team_side == "home" else -1.0

        pts_coeff = config.stat_coefficients["points"] * _effective_multiplier(config, player.position, "points")

        # Rebounds and assists are routed through their dedicated calibration
        # layers rather than the (degenerate) ridge coefficients.
        reb_contribution = ReboundDelta(
            delta_reb=player.rebounds_delta,
            position=player.position,
        ).margin_contribution()
        ast_contribution = AssistDelta(
            delta_ast=player.assists_delta,
        ).margin_contribution()

        contribution = (
            pts_coeff * player.points_delta
            + reb_contribution
            + ast_contribution
        )
        total += sign * contribution
    return total


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Run sample player-margin-delta scenarios against a position-weight config.")
    parser.add_argument(
        "--config",
        type=Path,
        default=project_root / "configs" / "position_weights.yaml",
        help="Path to a position_weights YAML",
    )
    args = parser.parse_args()

    print(f"Loading config from {args.config}...")
    config = PositionWeightConfig.from_yaml(args.config)

    scenarios: dict[str, list[PlayerDelta]] = {
        "home_star_guard_plus": [
            PlayerDelta("home_g1", "home", "G", 5.0, 1.0, 2.0),
        ],
        "away_center_dominant": [
            PlayerDelta("away_c1", "away", "C", 4.0, 4.0, 0.0),
        ],
        "balanced_home_plus_away_minus": [
            PlayerDelta("home_g2", "home", "G", 3.0, 0.0, 2.0),
            PlayerDelta("home_f1", "home", "F", 2.0, 2.0, 1.0),
            PlayerDelta("away_g1", "away", "G", -2.0, 0.0, -1.0),
        ],
    }

    print(f"Default position: {config.default_position}")
    print(f"Stat coefficients: {config.stat_coefficients}")
    print("Scenario margin deltas:")
    for name, players in scenarios.items():
        delta = compute_player_margin_delta(players, config)
        print(f"  {name}: {delta:+.3f}")


if __name__ == "__main__":
    main()

