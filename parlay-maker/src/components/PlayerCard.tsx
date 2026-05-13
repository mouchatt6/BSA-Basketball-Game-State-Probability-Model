import { useState } from "react";
import type { Player, StatType, ParlayLeg } from "../types";
import { formatOdds } from "../utils";

interface Props {
  player: Player;
  onAddLeg: (leg: ParlayLeg) => void;
  addedLegs: ParlayLeg[];
}

const DISPLAYED_STATS: StatType[] = ["points", "rebounds", "assists"];

const STAT_LABELS: Record<StatType, string> = {
  points: "Points",
  rebounds: "Rebounds",
  assists: "Assists",
  threes: "3-Pointers",
  steals: "Steals",
  blocks: "Blocks",
};

// Range around the default line the slider spans
const STAT_RANGE: Record<StatType, { min: number; max: number; step: number }> = {
  points: { min: 0, max: 60, step: 0.5 },
  rebounds: { min: 0, max: 25, step: 0.5 },
  assists: { min: 0, max: 20, step: 0.5 },
  threes: { min: 0, max: 10, step: 0.5 },
  steals: { min: 0, max: 5, step: 0.5 },
  blocks: { min: 0, max: 5, step: 0.5 },
};

// Rough implied probability given distance from the default line
function likelihood(value: number, baseline: number): number {
  const delta = (value - baseline) / Math.max(baseline, 1);
  // higher value = harder to go over = lower likelihood
  const raw = 0.5 - delta * 0.5;
  return Math.min(0.95, Math.max(0.05, raw));
}

function likelihoodLabel(pct: number): string {
  if (pct >= 0.85) return "Very Likely";
  if (pct >= 0.65) return "Likely";
  if (pct >= 0.45) return "Even";
  if (pct >= 0.25) return "Unlikely";
  return "Long Shot";
}

function likelihoodColor(pct: number): string {
  if (pct >= 0.65) return "#22c55e";
  if (pct >= 0.45) return "#f59e0b";
  return "#ef4444";
}

interface StatSliderProps {
  stat: StatType;
  baseline: number;
  value: number;
  onChange: (v: number) => void;
  selected: boolean;
  direction: "over" | "under";
  onSelect: () => void;
}

function StatSlider({ stat, baseline, value, onChange, selected, direction, onSelect }: StatSliderProps) {
  const { min, max, step } = STAT_RANGE[stat];
  const pct = direction === "over"
    ? likelihood(value, baseline)
    : 1 - likelihood(value, baseline);
  const thumbPct = ((value - min) / (max - min)) * 100;

  return (
    <div
      className={`stat-row ${selected ? "stat-row--selected" : ""}`}
      onClick={onSelect}
    >
      <div className="stat-row__header">
        <span className="stat-row__label">{STAT_LABELS[stat]}: <strong>{value % 1 === 0 ? value : value.toFixed(1)}</strong></span>
        <span
          className="stat-row__likelihood"
          style={{ color: likelihoodColor(pct) }}
        >
          {Math.round(pct * 100)}% likelihood
        </span>
      </div>
      <div className="stat-slider-track-wrap">
        <input
          type="range"
          className="stat-slider"
          min={min}
          max={max}
          step={step}
          value={value}
          style={{ "--thumb-pct": `${thumbPct}%`, "--track-color": likelihoodColor(pct) } as React.CSSProperties}
          onChange={(e) => { e.stopPropagation(); onChange(Number(e.target.value)); }}
          onClick={(e) => e.stopPropagation()}
        />
      </div>
      <div className="stat-row__sub">
        <span className="stat-row__baseline">Line: {baseline}</span>
        <span className="stat-row__status" style={{ color: likelihoodColor(pct) }}>
          {likelihoodLabel(pct)}
        </span>
      </div>
    </div>
  );
}

export default function PlayerCard({ player, onAddLeg, addedLegs }: Props) {
  const [selectedStat, setSelectedStat] = useState<StatType>("points");
  const [direction, setDirection] = useState<"over" | "under">("over");
  const [values, setValues] = useState<Record<StatType, number>>(() => {
    const init = {} as Record<StatType, number>;
    (Object.keys(player.props) as StatType[]).forEach((s) => {
      init[s] = player.props[s].line;
    });
    return init;
  });

  const prop = player.props[selectedStat];
  const currentValue = values[selectedStat];

  const isAdded = addedLegs.some(
    (l) =>
      l.player.id === player.id &&
      l.prop.stat === selectedStat &&
      l.prop.direction === direction
  );

  function handleAdd() {
    if (isAdded) return;
    onAddLeg({
      player,
      prop: {
        stat: selectedStat,
        line: currentValue,
        direction,
        odds: prop.avgOdds + (direction === "under" ? 5 : 0),
      },
    });
  }

  const initials = player.name.split(" ").map((n) => n[0]).join("");

  return (
    <div className="player-card">
      <div className="player-card__header">
        <div
          className="player-card__avatar"
          style={{ background: `${player.teamColor}33`, border: `2px solid ${player.teamColor}` }}
        >
          <span style={{ color: player.teamColor }}>{initials}</span>
        </div>
        <div className="player-card__info">
          <h3>{player.name}</h3>
          <span className="player-card__meta">
            <span className="player-card__team-dot" style={{ background: player.teamColor }} />
            {player.position}
          </span>
        </div>
        <div className="player-card__dir-toggle">
          <button
            className={`dir-btn ${direction === "over" ? "dir-btn--over" : ""}`}
            onClick={() => setDirection("over")}
          >
            Over
          </button>
          <button
            className={`dir-btn ${direction === "under" ? "dir-btn--under" : ""}`}
            onClick={() => setDirection("under")}
          >
            Under
          </button>
        </div>
      </div>

      <div className="stat-rows">
        {DISPLAYED_STATS.map((s) => (
          <StatSlider
            key={s}
            stat={s}
            baseline={player.props[s].line}
            value={values[s]}
            onChange={(v) => setValues((prev) => ({ ...prev, [s]: v }))}
            selected={selectedStat === s}
            direction={direction}
            onSelect={() => setSelectedStat(s)}
          />
        ))}
      </div>

      <div className="player-card__footer">
        <div className="footer-odds">
          <span className="footer-odds__label">Odds</span>
          <span className="footer-odds__value">{formatOdds(prop.avgOdds)}</span>
        </div>
        <button
          className={`add-leg-btn ${isAdded ? "add-leg-btn--added" : ""}`}
          onClick={handleAdd}
          disabled={isAdded}
        >
          {isAdded ? "✓ Added" : "+ Add to Parlay"}
        </button>
      </div>
    </div>
  );
}
