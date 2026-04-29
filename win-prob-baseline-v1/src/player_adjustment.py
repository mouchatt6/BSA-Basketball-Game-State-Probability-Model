from __future__ import annotations

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

