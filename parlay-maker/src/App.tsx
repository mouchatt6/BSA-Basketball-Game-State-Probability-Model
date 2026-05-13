import { useState } from "react";
import type { ParlayLeg } from "./types";
import { PLAYERS, GAMES } from "./data";
import PlayerCard from "./components/PlayerCard";
import ParlaySlip from "./components/ParlaySlip";
import GameFilter from "./components/GameFilter";
import "./App.css";

const TEAM_TO_GAME: Record<string, string> = {};
GAMES.forEach((g) => {
  TEAM_TO_GAME[g.homeTeam] = g.id;
  TEAM_TO_GAME[g.awayTeam] = g.id;
});

export default function App() {
  const [legs, setLegs] = useState<ParlayLeg[]>([]);
  const [selectedGame, setSelectedGame] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [slipOpen, setSlipOpen] = useState(false);

  function addLeg(leg: ParlayLeg) {
    setLegs((prev) => [...prev, leg]);
    setSlipOpen(true);
  }

  function removeLeg(index: number) {
    setLegs((prev) => prev.filter((_, i) => i !== index));
  }

  const filteredPlayers = PLAYERS.filter((p) => {
    const matchesGame = selectedGame ? TEAM_TO_GAME[p.team] === selectedGame : true;
    const matchesSearch =
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.team.toLowerCase().includes(search.toLowerCase());
    return matchesGame && matchesSearch;
  });

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header__brand">
          <span className="app-header__logo">🏀</span>
          <h1>Parlay Maker</h1>
          <span className="app-header__badge">NBA Props</span>
        </div>
        <div className="app-header__right">
          <span className="app-header__date">
            {new Date().toLocaleDateString("en-US", {
              weekday: "long",
              month: "long",
              day: "numeric",
            })}
          </span>
          <button
            className={`slip-toggle-btn ${legs.length > 0 ? "slip-toggle-btn--active" : ""}`}
            onClick={() => setSlipOpen((v) => !v)}
          >
            🎟️ Slip
            {legs.length > 0 && <span className="slip-badge">{legs.length}</span>}
          </button>
        </div>
      </header>

      <div className="app-body">
        <main className="app-main">
          <GameFilter
            games={GAMES}
            selectedGame={selectedGame}
            onSelectGame={setSelectedGame}
          />

          <div className="players-toolbar">
            <h2>
              Player Props
              <span className="players-count">{filteredPlayers.length} players</span>
            </h2>
            <input
              className="search-input"
              type="text"
              placeholder="Search players or teams..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className="players-grid">
            {filteredPlayers.map((p) => (
              <PlayerCard
                key={p.id}
                player={p}
                onAddLeg={addLeg}
                addedLegs={legs}
              />
            ))}
            {filteredPlayers.length === 0 && (
              <div className="no-results">No players found for this selection.</div>
            )}
          </div>
        </main>

        <aside className={`app-sidebar ${slipOpen ? "app-sidebar--open" : ""}`}>
          <ParlaySlip legs={legs} onRemoveLeg={removeLeg} onClear={() => setLegs([])} />
        </aside>
      </div>
    </div>
  );
}
