import { motion } from "motion/react";
import { LiveGame } from "../../data/mockData";
import { Badge } from "../ui/badge";

interface LiveGameTickerProps {
  game: LiveGame;
  selected?: boolean;
  onClick?: () => void;
}

export function LiveGameTicker({ game, selected, onClick }: LiveGameTickerProps) {
  const isLive = game.status === "live";

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      onClick={onClick}
      className={`cursor-pointer px-4 py-3 rounded-lg border transition-all ${
        selected
          ? "bg-slate-800/80 border-slate-600"
          : "bg-slate-900/50 border-slate-800/50 hover:bg-slate-800/60"
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold text-white">
              {game.awayTeam}
            </span>
            <span className="text-xs text-slate-500">@</span>
            <span className="text-xs font-semibold text-white">
              {game.homeTeam}
            </span>
          </div>
          {isLive ? (
            <div className="flex items-center gap-2">
              <span className="text-sm font-mono text-slate-300">
                {game.awayScore} - {game.homeScore}
              </span>
              <span className="text-xs text-slate-500">{game.quarter}</span>
              <span className="text-xs text-slate-500">{game.timeRemaining}</span>
            </div>
          ) : (
            <div className="text-xs text-slate-500">
              {game.startTime.toLocaleTimeString("en-US", {
                hour: "numeric",
                minute: "2-digit",
              })}
            </div>
          )}
        </div>
        {isLive && (
          <Badge className="bg-red-500/20 text-red-400 border-red-500/30 text-xs animate-pulse">
            LIVE
          </Badge>
        )}
      </div>
    </motion.div>
  );
}
