import { useState } from "react";
import { motion } from "motion/react";
import {
  TrendingUp,
  Filter,
  Search,
  BarChart3,
  Wallet,
  Settings,
} from "lucide-react";
import { MarketCard } from "../components/shared/MarketCard";
import { LiveGameTicker } from "../components/shared/LiveGameTicker";
import { liveGames, marketOpportunities } from "../data/mockData";
import { Input } from "../components/ui/input";
import { Button } from "../components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "../components/ui/tabs";
import { useNavigate } from "react-router";

export default function Dashboard() {
  const [selectedGame, setSelectedGame] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState("ev");
  const navigate = useNavigate();

  const filteredMarkets = selectedGame
    ? marketOpportunities.filter((m) => m.gameId === selectedGame)
    : marketOpportunities;

  const sortedMarkets = [...filteredMarkets].sort((a, b) => {
    if (sortBy === "ev") return Math.abs(b.ev) - Math.abs(a.ev);
    if (sortBy === "confidence") return b.confidence - a.confidence;
    if (sortBy === "liquidity") return b.liquidity - a.liquidity;
    return 0;
  });

  const positiveEVCount = marketOpportunities.filter((m) => m.ev > 0).length;
  const avgEV = (
    marketOpportunities.reduce((sum, m) => sum + m.ev, 0) /
    marketOpportunities.length
  ).toFixed(1);
  const totalLiquidity = marketOpportunities.reduce(
    (sum, m) => sum + m.liquidity,
    0
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800/50 bg-slate-900/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-lg flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white tracking-tight">
                    Arbitrage Engine
                  </h1>
                  <p className="text-xs text-slate-400">
                    NBA Prediction Markets
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 ml-6">
                <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                  {positiveEVCount} Opportunities
                </Badge>
                <Badge
                  variant="outline"
                  className="border-slate-700 text-slate-300"
                >
                  Avg EV: +{avgEV}%
                </Badge>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="sm"
                className="text-slate-400 hover:text-white"
              >
                <BarChart3 className="w-4 h-4 mr-2" />
                Analytics
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate("/portfolio")}
                className="text-slate-400 hover:text-white"
              >
                <Wallet className="w-4 h-4 mr-2" />
                Portfolio
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="text-slate-400 hover:text-white"
              >
                <Settings className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Left Sidebar - Live Games */}
          <div className="col-span-3">
            <div className="sticky top-24">
              <div className="mb-4">
                <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
                  Live Games
                </h2>
                <div className="space-y-2">
                  <LiveGameTicker
                    game={{
                      id: "all",
                      homeTeam: "All",
                      awayTeam: "Games",
                      homeScore: 0,
                      awayScore: 0,
                      quarter: "",
                      timeRemaining: "",
                      status: "upcoming",
                      startTime: new Date(),
                    }}
                    selected={selectedGame === null}
                    onClick={() => setSelectedGame(null)}
                  />
                  {liveGames.map((game) => (
                    <LiveGameTicker
                      key={game.id}
                      game={game}
                      selected={selectedGame === game.id}
                      onClick={() => setSelectedGame(game.id)}
                    />
                  ))}
                </div>
              </div>

              {/* Market Stats */}
              <div className="mt-6 p-4 rounded-lg bg-slate-900/50 border border-slate-800/50">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                  Market Overview
                </h3>
                <div className="space-y-3">
                  <div>
                    <div className="text-xs text-slate-500 mb-1">
                      Total Liquidity
                    </div>
                    <div className="text-lg font-bold text-white font-mono">
                      ${(totalLiquidity / 1000000).toFixed(2)}M
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500 mb-1">
                      Active Markets
                    </div>
                    <div className="text-lg font-bold text-white font-mono">
                      {marketOpportunities.length}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-500 mb-1">
                      Avg Confidence
                    </div>
                    <div className="text-lg font-bold text-emerald-400 font-mono">
                      {(
                        marketOpportunities.reduce(
                          (sum, m) => sum + m.confidence,
                          0
                        ) / marketOpportunities.length
                      ).toFixed(1)}
                      %
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Main Content - Market Cards */}
          <div className="col-span-9">
            {/* Controls */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <Tabs defaultValue="all" className="w-auto">
                  <TabsList className="bg-slate-900/50 border border-slate-800/50">
                    <TabsTrigger value="all">All Markets</TabsTrigger>
                    <TabsTrigger value="positive">Positive EV</TabsTrigger>
                    <TabsTrigger value="high-confidence">
                      High Confidence
                    </TabsTrigger>
                  </TabsList>
                </Tabs>
              </div>

              <div className="flex items-center gap-3">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                  <Input
                    placeholder="Search players..."
                    className="pl-10 w-64 bg-slate-900/50 border-slate-800/50 text-white placeholder:text-slate-500"
                  />
                </div>

                <Select value={sortBy} onValueChange={setSortBy}>
                  <SelectTrigger className="w-40 bg-slate-900/50 border-slate-800/50 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-900 border-slate-800">
                    <SelectItem value="ev">Sort by EV</SelectItem>
                    <SelectItem value="confidence">
                      Sort by Confidence
                    </SelectItem>
                    <SelectItem value="liquidity">
                      Sort by Liquidity
                    </SelectItem>
                  </SelectContent>
                </Select>

                <Button
                  variant="outline"
                  size="icon"
                  className="border-slate-800/50 hover:bg-slate-800/50"
                >
                  <Filter className="w-4 h-4" />
                </Button>
              </div>
            </div>

            {/* Market Grid */}
            <motion.div
              layout
              className="grid grid-cols-2 gap-4"
            >
              {sortedMarkets.map((market, idx) => (
                <motion.div
                  key={market.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.05 }}
                >
                  <MarketCard market={market} />
                </motion.div>
              ))}
            </motion.div>

            {sortedMarkets.length === 0 && (
              <div className="text-center py-12">
                <p className="text-slate-500">No markets found</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
