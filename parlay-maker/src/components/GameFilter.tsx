import type { Game } from "../types";

interface Props {
  games: Game[];
  selectedGame: string | null;
  onSelectGame: (id: string | null) => void;
}

export default function GameFilter({ games, selectedGame, onSelectGame }: Props) {
  return (
    <div className="game-filter">
      <h2>Today's Games</h2>
      <div className="game-filter__list">
        <button
          className={`game-chip ${selectedGame === null ? "game-chip--active" : ""}`}
          onClick={() => onSelectGame(null)}
        >
          All Games
        </button>
        {games.map((g) => (
          <button
            key={g.id}
            className={`game-chip ${selectedGame === g.id ? "game-chip--active" : ""}`}
            onClick={() => onSelectGame(selectedGame === g.id ? null : g.id)}
          >
            <span className="game-chip__team">
              <span className="game-chip__dot" style={{ background: g.awayColor }} />
              {g.awayTeam.split(" ").pop()}
            </span>
            <span className="game-chip__vs">@</span>
            <span className="game-chip__team">
              <span className="game-chip__dot" style={{ background: g.homeColor }} />
              {g.homeTeam.split(" ").pop()}
            </span>
            <span className="game-chip__time">{g.time}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
