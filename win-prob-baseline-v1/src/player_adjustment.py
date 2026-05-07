from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

TeamSide = Literal["home", "away"]


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
        reb_coeff = config.stat_coefficients["rebounds"] * _effective_multiplier(config, player.position, "rebounds")
        ast_coeff = config.stat_coefficients["assists"] * _effective_multiplier(config, player.position, "assists")

        contribution = (
            pts_coeff * player.points_delta
            + reb_coeff * player.rebounds_delta
            + ast_coeff * player.assists_delta
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

