import { motion } from "motion/react";
import { TrendingUp, TrendingDown, Activity, DollarSign, Droplet } from "lucide-react";
import { Card } from "../ui/card";
import { Badge } from "../ui/badge";
import { MarketOpportunity } from "../../data/mockData";
import { useNavigate } from "react-router";

interface MarketCardProps {
  market: MarketOpportunity;
}

export function MarketCard({ market }: MarketCardProps) {
  const navigate = useNavigate();
  const isPositiveEV = market.ev > 0;
  const evColor = isPositiveEV ? "text-yellow-400" : "text-pink-500";
  const glowColor = isPositiveEV
    ? "shadow-yellow-500/20"
    : "shadow-pink-500/20";

  return (
    <motion.div
      whileHover={{ scale: 1.01, y: -2 }}
      transition={{ duration: 0.2 }}
      onClick={() => navigate(`/market/${market.id}`)}
      className="cursor-pointer"
    >
      <Card
        className={`relative bg-gradient-to-br from-slate-900/90 to-slate-950/90 border-slate-800/50 backdrop-blur-sm overflow-hidden ${
          isPositiveEV ? "hover:shadow-lg hover:shadow-yellow-500/10" : ""
        }`}
      >
        {/* Glow effect for positive EV */}
        {isPositiveEV && market.ev > 10 && (
          <div className="absolute inset-0 bg-gradient-to-r from-yellow-500/5 to-transparent pointer-events-none" />
        )}

        <div className="p-4 space-y-3">
          {/* Header */}
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm font-medium text-slate-400">
                  {market.team} vs {market.opponent}
                </span>
                <Badge
                  variant="outline"
                  className="text-xs border-slate-700 bg-slate-800/50"
                >
                  {market.sportsbook}
                </Badge>
              </div>
              <h3 className="text-lg font-semibold text-white">
                {market.player}
              </h3>
              <p className="text-sm text-slate-400">
                {market.statType}{" "}
                <span className="text-white font-mono">
                  O {market.line}
                </span>
              </p>
            </div>

            {/* EV Badge */}
            <div
              className={`flex flex-col items-end gap-1 ${
                isPositiveEV ? "animate-pulse" : ""
              }`}
            >
              <div
                className={`text-2xl font-bold ${evColor} flex items-center gap-1`}
              >
                {isPositiveEV ? "+" : ""}
                {market.ev.toFixed(1)}%
                {isPositiveEV ? (
                  <TrendingUp className="w-5 h-5" />
                ) : (
                  <TrendingDown className="w-5 h-5" />
                )}
              </div>
              <span className="text-xs text-slate-500">Expected Value</span>
            </div>
          </div>

          {/* Probability Comparison */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-slate-800/50 rounded-lg p-2.5 border border-slate-700/50">
              <div className="text-xs text-slate-400 mb-1">Market Prob</div>
              <div className="text-xl font-bold text-slate-200">
                {market.marketProb}%
              </div>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-2.5 border border-slate-700/50">
              <div className="text-xs text-slate-400 mb-1">Model Prob</div>
              <div className={`text-xl font-bold ${evColor}`}>
                {market.modelProb}%
              </div>
            </div>
          </div>

          {/* Metrics Row */}
          <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800">
            <div className="flex flex-col">
              <div className="flex items-center gap-1 text-xs text-slate-500">
                <Activity className="w-3 h-3" />
                Confidence
              </div>
              <div className="text-sm font-semibold text-slate-300 font-mono">
                {market.confidence}%
              </div>
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-1 text-xs text-slate-500">
                <DollarSign className="w-3 h-3" />
                Kelly
              </div>
              <div className="text-sm font-semibold text-slate-300 font-mono">
                {market.kelly.toFixed(1)}%
              </div>
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-1 text-xs text-slate-500">
                <Droplet className="w-3 h-3" />
                Liquidity
              </div>
              <div className="text-sm font-semibold text-slate-300 font-mono">
                ${(market.liquidity / 1000).toFixed(0)}K
              </div>
            </div>
          </div>

          {/* Sharp vs Public Indicator */}
          <div className="flex items-center justify-between pt-2 border-t border-slate-800">
            <div className="flex items-center gap-2">
              <div className="text-xs text-slate-500">Sharp:</div>
              <Badge
                variant={
                  market.sharpMoney === "over" ? "default" : "outline"
                }
                className={`text-xs ${
                  market.sharpMoney === "over"
                    ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                    : "border-slate-700"
                }`}
              >
                {market.sharpMoney}
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              <div className="text-xs text-slate-500">Public:</div>
              <Badge
                variant="outline"
                className="text-xs border-slate-700 text-slate-400"
              >
                {market.publicMoney}
              </Badge>
            </div>
          </div>

          {/* Mini Sparkline (simplified) */}
          <div className="h-8 flex items-end gap-1">
            {market.lineMovement.map((value, idx) => {
              const maxValue = Math.max(...market.lineMovement);
              const minValue = Math.min(...market.lineMovement);
              const range = maxValue - minValue || 1;
              const height = ((value - minValue) / range) * 100;
              return (
                <div
                  key={idx}
                  className="flex-1 bg-gradient-to-t from-slate-600 to-slate-500 rounded-sm opacity-50"
                  style={{ height: `${Math.max(height, 20)}%` }}
                />
              );
            })}
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
