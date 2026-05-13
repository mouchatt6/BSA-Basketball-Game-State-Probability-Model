import { useState } from "react";
import type { ParlayLeg } from "../types";
import { calcParlayOdds, calcPayout, formatOdds } from "../utils";

interface Props {
  legs: ParlayLeg[];
  onRemoveLeg: (index: number) => void;
  onClear: () => void;
}

export default function ParlaySlip({ legs, onRemoveLeg, onClear }: Props) {
  const [stake, setStake] = useState<number>(10);

  const parlayOdds = legs.length > 0 ? calcParlayOdds(legs.map((l) => l.prop.odds)) : 0;
  const payout = legs.length > 0 ? calcPayout(stake, parlayOdds) : 0;

  return (
    <div className="parlay-slip">
      <div className="parlay-slip__header">
        <div className="parlay-slip__title">
          <span className="parlay-slip__icon">🎟️</span>
          <h2>Parlay Slip</h2>
          <span className="parlay-slip__count">{legs.length}</span>
        </div>
        {legs.length > 0 && (
          <button className="clear-btn" onClick={onClear}>
            Clear All
          </button>
        )}
      </div>

      {legs.length === 0 ? (
        <div className="parlay-slip__empty">
          <p>Add player props to build your parlay</p>
          <span>Select a player and click "+ Add to Parlay"</span>
        </div>
      ) : (
        <>
          <div className="parlay-slip__legs">
            {legs.map((leg, i) => (
              <div key={i} className="parlay-leg">
                <div className="parlay-leg__left">
                  <div
                    className="parlay-leg__dot"
                    style={{ background: leg.player.teamColor }}
                  />
                  <div className="parlay-leg__info">
                    <span className="parlay-leg__player">{leg.player.name}</span>
                    <span className="parlay-leg__desc">
                      {leg.prop.direction === "over" ? "Over" : "Under"}{" "}
                      {leg.prop.line} {capitalize(leg.prop.stat)}
                    </span>
                  </div>
                </div>
                <div className="parlay-leg__right">
                  <span
                    className={`parlay-leg__odds ${leg.prop.odds > 0 ? "odds--pos" : "odds--neg"}`}
                  >
                    {formatOdds(leg.prop.odds)}
                  </span>
                  <button
                    className="remove-leg-btn"
                    onClick={() => onRemoveLeg(i)}
                    title="Remove"
                  >
                    ×
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="parlay-slip__summary">
            <div className="summary-row">
              <span>Parlay Odds</span>
              <span
                className={`summary-odds ${parlayOdds > 0 ? "odds--pos" : "odds--neg"}`}
              >
                {formatOdds(parlayOdds)}
              </span>
            </div>

            <div className="stake-row">
              <span>Stake ($)</span>
              <div className="stake-inputs">
                {[5, 10, 25, 50].map((v) => (
                  <button
                    key={v}
                    className={`stake-preset ${stake === v ? "stake-preset--active" : ""}`}
                    onClick={() => setStake(v)}
                  >
                    ${v}
                  </button>
                ))}
                <input
                  type="number"
                  className="stake-input"
                  value={stake}
                  min={1}
                  onChange={(e) => setStake(Math.max(1, Number(e.target.value)))}
                />
              </div>
            </div>

            <div className="summary-row summary-row--payout">
              <span>Potential Payout</span>
              <span className="payout-value">${payout.toFixed(2)}</span>
            </div>

            <button className="place-btn">Place Parlay</button>
          </div>
        </>
      )}
    </div>
  );
}

function capitalize(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}
