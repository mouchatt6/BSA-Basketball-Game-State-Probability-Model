import { useState } from "react";
import { useParams, useNavigate } from "react-router";
import { motion } from "motion/react";
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  Target,
  AlertTriangle,
  CheckCircle2,
  BarChart3,
} from "lucide-react";
import { marketOpportunities } from "../data/mockData";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Slider } from "../components/ui/slider";
import { Input } from "../components/ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

export default function PlayerMarketDetail() {
  const { marketId } = useParams();
  const navigate = useNavigate();
  const [kellyFraction, setKellyFraction] = useState([50]);
  const [customStake, setCustomStake] = useState("");

  const market = marketOpportunities.find((m) => m.id === marketId);

  if (!market) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-500">Market not found</p>
          <Button onClick={() => navigate("/")} className="mt-4">
            Back to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  const isPositiveEV = market.ev > 0;

  // Generate probability distribution data
  const probabilityData = Array.from({ length: 21 }, (_, i) => {
    const value = market.line - 10 + i;
    const modelProb = Math.max(
      0,
      100 * Math.exp(-Math.pow((value - market.line) / 5, 2))
    );
    const marketProb = Math.max(
      0,
      100 * Math.exp(-Math.pow((value - market.line + 2) / 5, 2))
    );
    return {
      value,
      modelProb,
      marketProb,
    };
  });

  // Line movement over time
  const lineMovementData = market.lineMovement.map((prob, idx) => ({
    time: `${idx * 5}m`,
    probability: prob,
  }));

  // Related markets (mock data)
  const relatedMarkets = [
    { stat: "Assists", line: 6.5, ev: 4.2 },
    { stat: "Rebounds", line: 4.5, ev: -2.1 },
    { stat: "3PT Made", line: 3.5, ev: 8.7 },
    { stat: "Pts + Reb + Ast", line: 42.5, ev: 11.3 },
  ];

  const recommendedStake = (market.kelly * kellyFraction[0]) / 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800/50 bg-slate-900/50 backdrop-blur-xl sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => navigate("/")}
                className="text-slate-400 hover:text-white"
              >
                <ArrowLeft className="w-5 h-5" />
              </Button>
              <div>
                <h1 className="text-xl font-bold text-white">
                  {market.player} · {market.statType}
                </h1>
                <p className="text-sm text-slate-400">
                  {market.team} vs {market.opponent} · {market.sportsbook}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-sm text-slate-400">Expected Value</div>
                <div
                  className={`text-3xl font-bold ${
                    isPositiveEV ? "text-yellow-400" : "text-pink-500"
                  }`}
                >
                  {isPositiveEV ? "+" : ""}
                  {market.ev.toFixed(1)}%
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Main Content */}
          <div className="col-span-8 space-y-6">
            {/* Probability Comparison */}
            <Card className="bg-gradient-to-br from-slate-900/90 to-slate-950/90 border-slate-800/50 p-6">
              <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Probability Analysis
              </h2>

              {/* Side-by-side comparison */}
              <div className="grid grid-cols-2 gap-6 mb-6">
                <div className="text-center p-6 rounded-lg bg-slate-800/30 border border-slate-700/30">
                  <div className="text-sm text-slate-400 mb-2">
                    Market Implied
                  </div>
                  <div className="text-5xl font-bold text-slate-200 mb-2">
                    {market.marketProb}%
                  </div>
                  <div className="text-xs text-slate-500">
                    {market.sportsbook} Odds
                  </div>
                </div>

                <div
                  className={`text-center p-6 rounded-lg border ${
                    isPositiveEV
                      ? "bg-yellow-500/5 border-yellow-500/30"
                      : "bg-pink-500/5 border-pink-500/30"
                  }`}
                >
                  <div className="text-sm text-slate-400 mb-2">
                    Model Probability
                  </div>
                  <div
                    className={`text-5xl font-bold mb-2 ${
                      isPositiveEV ? "text-yellow-400" : "text-pink-500"
                    }`}
                  >
                    {market.modelProb}%
                  </div>
                  <div className="text-xs text-slate-500">
                    Quantitative Model
                  </div>
                </div>
              </div>

              {/* Probability Distribution Chart */}
              <div className="h-64 mt-6">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={probabilityData}>
                    <defs>
                      <linearGradient
                        id="modelGradient"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="5%"
                          stopColor="#fbbf24"
                          stopOpacity={0.3}
                        />
                        <stop
                          offset="95%"
                          stopColor="#fbbf24"
                          stopOpacity={0}
                        />
                      </linearGradient>
                      <linearGradient
                        id="marketGradient"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="5%"
                          stopColor="#94a3b8"
                          stopOpacity={0.3}
                        />
                        <stop
                          offset="95%"
                          stopColor="#94a3b8"
                          stopOpacity={0}
                        />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis
                      dataKey="value"
                      stroke="#64748b"
                      tick={{ fill: "#64748b" }}
                    />
                    <YAxis stroke="#64748b" tick={{ fill: "#64748b" }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1e293b",
                        border: "1px solid #334155",
                        borderRadius: "8px",
                      }}
                      labelStyle={{ color: "#e2e8f0" }}
                    />
                    <ReferenceLine
                      x={market.line}
                      stroke="#ef4444"
                      strokeDasharray="3 3"
                      label={{ value: "Line", fill: "#ef4444" }}
                    />
                    <Area
                      type="monotone"
                      dataKey="marketProb"
                      stroke="#94a3b8"
                      fillOpacity={1}
                      fill="url(#marketGradient)"
                      name="Market"
                    />
                    <Area
                      type="monotone"
                      dataKey="modelProb"
                      stroke="#fbbf24"
                      fillOpacity={1}
                      fill="url(#modelGradient)"
                      name="Model"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </Card>

            {/* Line Movement */}
            <Card className="bg-gradient-to-br from-slate-900/90 to-slate-950/90 border-slate-800/50 p-6">
              <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Line Movement
              </h2>

              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={lineMovementData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis
                      dataKey="time"
                      stroke="#64748b"
                      tick={{ fill: "#64748b" }}
                    />
                    <YAxis
                      stroke="#64748b"
                      tick={{ fill: "#64748b" }}
                      domain={[40, 65]}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1e293b",
                        border: "1px solid #334155",
                        borderRadius: "8px",
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="probability"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={{ fill: "#3b82f6", r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="grid grid-cols-3 gap-4 mt-6">
                <div className="p-3 rounded-lg bg-slate-800/30 border border-slate-700/30">
                  <div className="text-xs text-slate-500 mb-1">
                    Opening Line
                  </div>
                  <div className="text-lg font-semibold text-slate-300">
                    {market.lineMovement[0]}%
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-slate-800/30 border border-slate-700/30">
                  <div className="text-xs text-slate-500 mb-1">
                    Current Line
                  </div>
                  <div className="text-lg font-semibold text-white">
                    {market.marketProb}%
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-slate-800/30 border border-slate-700/30">
                  <div className="text-xs text-slate-500 mb-1">Movement</div>
                  <div
                    className={`text-lg font-semibold ${
                      market.marketProb - market.lineMovement[0] > 0
                        ? "text-green-400"
                        : "text-red-400"
                    }`}
                  >
                    {market.marketProb - market.lineMovement[0] > 0 ? "+" : ""}
                    {(market.marketProb - market.lineMovement[0]).toFixed(1)}%
                  </div>
                </div>
              </div>
            </Card>

            {/* Model Insights */}
            <Card className="bg-gradient-to-br from-slate-900/90 to-slate-950/90 border-slate-800/50 p-6">
              <h2 className="text-lg font-semibold text-white mb-4">
                Model Insights
              </h2>

              <Tabs defaultValue="reasoning" className="w-full">
                <TabsList className="bg-slate-800/50 border border-slate-700/50 mb-4">
                  <TabsTrigger value="reasoning">Reasoning</TabsTrigger>
                  <TabsTrigger value="matchup">Matchup</TabsTrigger>
                  <TabsTrigger value="correlations">Correlations</TabsTrigger>
                </TabsList>

                <TabsContent value="reasoning" className="space-y-3">
                  <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-800/30">
                    <CheckCircle2 className="w-5 h-5 text-green-400 mt-0.5" />
                    <div>
                      <div className="text-sm font-medium text-white">
                        Strong Recent Form
                      </div>
                      <div className="text-xs text-slate-400 mt-1">
                        {market.player} averaging {market.line + 3.2} {market.statType.toLowerCase()} over last 5 games
                      </div>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-800/30">
                    <CheckCircle2 className="w-5 h-5 text-green-400 mt-0.5" />
                    <div>
                      <div className="text-sm font-medium text-white">
                        Favorable Matchup
                      </div>
                      <div className="text-xs text-slate-400 mt-1">
                        {market.opponent} ranks 27th in defensive rating vs {market.player}'s position
                      </div>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-800/30">
                    <AlertTriangle className="w-5 h-5 text-yellow-400 mt-0.5" />
                    <div>
                      <div className="text-sm font-medium text-white">
                        Increased Pace Expected
                      </div>
                      <div className="text-xs text-slate-400 mt-1">
                        Game projected at 104.5 possessions (+6.2 above league average)
                      </div>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="matchup" className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/30">
                      <div className="text-xs text-slate-500 mb-2">
                        Season Average
                      </div>
                      <div className="text-2xl font-bold text-white">
                        {market.line - 1.5}
                      </div>
                    </div>
                    <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/30">
                      <div className="text-xs text-slate-500 mb-2">
                        vs {market.opponent} (Last 3)
                      </div>
                      <div className="text-2xl font-bold text-green-400">
                        {market.line + 2.8}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/30">
                      <span className="text-sm text-slate-400">Usage Rate</span>
                      <span className="text-sm font-semibold text-white">
                        28.4%
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/30">
                      <span className="text-sm text-slate-400">
                        True Shooting %
                      </span>
                      <span className="text-sm font-semibold text-white">
                        61.2%
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/30">
                      <span className="text-sm text-slate-400">
                        Minutes Projection
                      </span>
                      <span className="text-sm font-semibold text-white">
                        35.2 min
                      </span>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="correlations" className="space-y-3">
                  <p className="text-sm text-slate-400 mb-3">
                    Related markets for {market.player}:
                  </p>
                  {relatedMarkets.map((related, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 rounded-lg bg-slate-800/30 border border-slate-700/30"
                    >
                      <div>
                        <div className="text-sm font-medium text-white">
                          {related.stat}
                        </div>
                        <div className="text-xs text-slate-500">
                          O/U {related.line}
                        </div>
                      </div>
                      <Badge
                        className={
                          related.ev > 0
                            ? "bg-green-500/20 text-green-400 border-green-500/30"
                            : "bg-red-500/20 text-red-400 border-red-500/30"
                        }
                      >
                        {related.ev > 0 ? "+" : ""}
                        {related.ev.toFixed(1)}% EV
                      </Badge>
                    </div>
                  ))}
                </TabsContent>
              </Tabs>
            </Card>
          </div>

          {/* Right Sidebar - Execution Panel */}
          <div className="col-span-4">
            <div className="sticky top-24 space-y-6">
              {/* Trade Recommendation */}
              <Card
                className={`bg-gradient-to-br border p-6 ${
                  isPositiveEV
                    ? "from-yellow-500/10 to-orange-500/10 border-yellow-500/30"
                    : "from-pink-500/10 to-red-500/10 border-pink-500/30"
                }`}
              >
                <div className="flex items-center gap-3 mb-4">
                  {isPositiveEV ? (
                    <TrendingUp className="w-6 h-6 text-yellow-400" />
                  ) : (
                    <TrendingDown className="w-6 h-6 text-pink-500" />
                  )}
                  <div>
                    <div className="text-sm text-slate-400">
                      Trade Signal
                    </div>
                    <div
                      className={`text-xl font-bold ${
                        isPositiveEV ? "text-yellow-400" : "text-pink-500"
                      }`}
                    >
                      {isPositiveEV ? "BUY OVER" : "PASS"}
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/50">
                    <span className="text-sm text-slate-400">Edge</span>
                    <span
                      className={`text-sm font-semibold ${
                        isPositiveEV ? "text-yellow-400" : "text-pink-500"
                      }`}
                    >
                      {isPositiveEV ? "+" : ""}
                      {market.ev.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/50">
                    <span className="text-sm text-slate-400">Confidence</span>
                    <span className="text-sm font-semibold text-white">
                      {market.confidence}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/50">
                    <span className="text-sm text-slate-400">Liquidity</span>
                    <span className="text-sm font-semibold text-white">
                      ${(market.liquidity / 1000).toFixed(0)}K
                    </span>
                  </div>
                </div>
              </Card>

              {/* Position Sizing */}
              {isPositiveEV && (
                <Card className="bg-gradient-to-br from-slate-900/90 to-slate-950/90 border-slate-800/50 p-6">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Target className="w-5 h-5" />
                    Position Sizing
                  </h3>

                  <div className="space-y-6">
                    {/* Kelly Fraction Slider */}
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <label className="text-sm text-slate-400">
                          Kelly Fraction
                        </label>
                        <span className="text-sm font-semibold text-white">
                          {kellyFraction[0]}%
                        </span>
                      </div>
                      <Slider
                        value={kellyFraction}
                        onValueChange={setKellyFraction}
                        max={100}
                        step={5}
                        className="mb-2"
                      />
                      <div className="flex justify-between text-xs text-slate-500">
                        <span>Conservative</span>
                        <span>Aggressive</span>
                      </div>
                    </div>

                    {/* Recommended Stake */}
                    <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/30">
                      <div className="text-xs text-slate-400 mb-1">
                        Recommended Stake
                      </div>
                      <div className="text-3xl font-bold text-yellow-400 mb-1">
                        ${recommendedStake.toFixed(0)}
                      </div>
                      <div className="text-xs text-slate-500">
                        {market.kelly.toFixed(1)}% of bankroll ×{" "}
                        {kellyFraction[0]}% fraction
                      </div>
                    </div>

                    {/* Custom Stake Input */}
                    <div>
                      <label className="text-sm text-slate-400 mb-2 block">
                        Custom Stake
                      </label>
                      <div className="relative">
                        <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                        <Input
                          type="number"
                          value={customStake}
                          onChange={(e) => setCustomStake(e.target.value)}
                          placeholder="Enter amount"
                          className="pl-10 bg-slate-900/50 border-slate-800/50 text-white"
                        />
                      </div>
                    </div>

                    {/* Expected ROI */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-3 rounded-lg bg-slate-800/30 border border-slate-700/30">
                        <div className="text-xs text-slate-500 mb-1">
                          Expected ROI
                        </div>
                        <div className="text-lg font-semibold text-green-400">
                          +{market.ev.toFixed(1)}%
                        </div>
                      </div>
                      <div className="p-3 rounded-lg bg-slate-800/30 border border-slate-700/30">
                        <div className="text-xs text-slate-500 mb-1">
                          Est. Slippage
                        </div>
                        <div className="text-lg font-semibold text-slate-300">
                          {market.slippage.toFixed(2)}%
                        </div>
                      </div>
                    </div>

                    {/* Execute Button */}
                    <Button className="w-full bg-yellow-500 hover:bg-yellow-600 text-slate-900 font-semibold">
                      Place Trade
                    </Button>
                  </div>
                </Card>
              )}

              {/* Risk Warnings */}
              <Card className="bg-slate-900/50 border-slate-800/50 p-4">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                  <div className="text-xs text-slate-400">
                    This is a quantitative model prediction. Past performance
                    does not guarantee future results. Trade responsibly.
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
