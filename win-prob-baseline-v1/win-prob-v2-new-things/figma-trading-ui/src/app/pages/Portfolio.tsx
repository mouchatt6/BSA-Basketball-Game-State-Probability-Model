import { motion } from "motion/react";
import { ArrowLeft, TrendingUp, TrendingDown, DollarSign, Target, Activity, BarChart3, PieChart } from "lucide-react";
import { useNavigate } from "react-router";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs";
import { positions, portfolioMetrics } from "../data/mockData";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
} from "recharts";

export default function Portfolio() {
  const navigate = useNavigate();

  // Generate PnL curve data
  const pnlData = Array.from({ length: 30 }, (_, i) => ({
    day: i + 1,
    pnl: Math.random() * 500 + i * 60 - 200,
  }));

  // Exposure by stat type
  const exposureData = [
    { name: "Points", value: 45, color: "#fbbf24" },
    { name: "Rebounds", value: 20, color: "#3b82f6" },
    { name: "Assists", value: 15, color: "#10b981" },
    { name: "Combos", value: 20, color: "#ec4899" },
  ];

  // Win rate by market type
  const performanceData = [
    { type: "Points", wins: 42, losses: 18, winRate: 70 },
    { type: "Rebounds", wins: 28, losses: 22, winRate: 56 },
    { type: "Assists", wins: 15, losses: 10, winRate: 60 },
    { type: "Combos", wins: 8, losses: 4, winRate: 67 },
  ];

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
                <h1 className="text-xl font-bold text-white">Portfolio</h1>
                <p className="text-sm text-slate-400">Risk & Performance Dashboard</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-sm text-slate-400">Total Value</div>
                <div className="text-2xl font-bold text-white font-mono">
                  ${portfolioMetrics.totalValue.toLocaleString()}
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-slate-400">Unrealized P&L</div>
                <div
                  className={`text-2xl font-bold font-mono ${
                    portfolioMetrics.unrealizedPnL > 0 ? "text-green-400" : "text-red-400"
                  }`}
                >
                  {portfolioMetrics.unrealizedPnL > 0 ? "+" : ""}$
                  {portfolioMetrics.unrealizedPnL.toLocaleString()}
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-6">
        {/* Top Metrics */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <Card className="bg-gradient-to-br from-slate-900/90 to-slate-950/90 border-slate-800/50 p-6">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-slate-400">Realized P&L</div>
              <DollarSign className="w-4 h-4 text-green-400" />
            </div>
            <div className="text-3xl font-bold text-green-400 mb-1">
              +${portfolioMetrics.realizedPnL.toLocaleString()}
            </div>
            <div className="text-xs text-slate-500">All-time gains</div>
          </Card>

          <Card className="bg-gradient-to-br from-slate-900/90 to-slate-950/90 border-slate-800/50 p-6">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-slate-400">Win Rate</div>
              <Target className="w-4 h-4 text-yellow-400" />
            </div>
            <div className="text-3xl font-bold text-yellow-400 mb-1">
              {portfolioMetrics.winRate}%
            </div>
            <div className="text-xs text-slate-500">
              {portfolioMetrics.totalTrades} total trades
            </div>
          </Card>

          <Card className="bg-gradient-to-br from-slate-900/90 to-slate-950/90 border-slate-800/50 p-6">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-slate-400">Sharpe Ratio</div>
              <Activity className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-3xl font-bold text-blue-400 mb-1">
              {portfolioMetrics.sharpeRatio}
            </div>
            <div className="text-xs text-slate-500">Risk-adjusted returns</div>
          </Card>

          <Card className="bg-gradient-to-br from-slate-900/90 to-slate-950/90 border-slate-800/50 p-6">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-slate-400">Avg EV</div>
              <TrendingUp className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-3xl font-bold text-emerald-400 mb-1">
              +{portfolioMetrics.avgEV}%
            </div>
            <div className="text-xs text-slate-500">Expected value</div>
          </Card>
        </div>

        <div className="grid grid-cols-12 gap-6">
          {/* Main Content */}
          <div className="col-span-8 space-y-6">
            {/* Active Positions */}
            <Card className="bg-gradient-to-br from-slate-900/90 to-slate-950/90 border-slate-800/50 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  Active Positions
                </h2>
                <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                  {positions.length} Open
                </Badge>
              </div>

              <div className="space-y-3">
                {positions.map((position) => (
                  <motion.div
                    key={position.id}
                    whileHover={{ scale: 1.01 }}
                    className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/30 hover:border-slate-600/50 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="text-base font-semibold text-white mb-1">
                          {position.player}
                        </h3>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-slate-400">
                            {position.statType}
                          </span>
                          <Badge
                            variant="outline"
                            className="text-xs border-slate-700"
                          >
                            {position.side.toUpperCase()} {position.line}
                          </Badge>
                        </div>
                      </div>
                      <div className="text-right">
                        <div
                          className={`text-xl font-bold ${
                            position.unrealizedPnL > 0
                              ? "text-green-400"
                              : "text-red-400"
                          }`}
                        >
                          {position.unrealizedPnL > 0 ? "+" : ""}$
                          {position.unrealizedPnL}
                        </div>
                        <div className="text-xs text-slate-500">
                          {position.expectedROI > 0 ? "+" : ""}
                          {position.expectedROI.toFixed(1)}% ROI
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-4 gap-3">
                      <div className="p-2 rounded bg-slate-900/50">
                        <div className="text-xs text-slate-500 mb-1">Stake</div>
                        <div className="text-sm font-semibold text-white font-mono">
                          ${position.stake}
                        </div>
                      </div>
                      <div className="p-2 rounded bg-slate-900/50">
                        <div className="text-xs text-slate-500 mb-1">Entry</div>
                        <div className="text-sm font-semibold text-slate-300 font-mono">
                          {position.entryProb}%
                        </div>
                      </div>
                      <div className="p-2 rounded bg-slate-900/50">
                        <div className="text-xs text-slate-500 mb-1">Current</div>
                        <div className="text-sm font-semibold text-slate-300 font-mono">
                          {position.currentProb}%
                        </div>
                      </div>
                      <div className="p-2 rounded bg-slate-900/50">
                        <div className="text-xs text-slate-500 mb-1">Time</div>
                        <div className="text-sm font-semibold text-slate-300">
                          {new Date(position.timestamp).toLocaleTimeString("en-US", {
                            hour: "numeric",
                            minute: "2-digit",
                          })}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </Card>

            {/* PnL Chart */}
            <Card className="bg-gradient-to-br from-slate-900/90 to-slate-950/90 border-slate-800/50 p-6">
              <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Cumulative P&L (30 Days)
              </h2>

              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={pnlData}>
                    <defs>
                      <linearGradient id="pnlGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis
                      dataKey="day"
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
                      formatter={(value: number) => [
                        `$${value.toFixed(0)}`,
                        "P&L",
                      ]}
                    />
                    <Area
                      type="monotone"
                      dataKey="pnl"
                      stroke="#10b981"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#pnlGradient)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </Card>

            {/* Performance by Market Type */}
            <Card className="bg-gradient-to-br from-slate-900/90 to-slate-950/90 border-slate-800/50 p-6">
              <h2 className="text-lg font-semibold text-white mb-6">
                Performance by Market Type
              </h2>

              <div className="space-y-4">
                {performanceData.map((item) => (
                  <div key={item.type}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-slate-400">{item.type}</span>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-slate-500">
                          {item.wins}W - {item.losses}L
                        </span>
                        <span className="text-sm font-semibold text-white font-mono">
                          {item.winRate}%
                        </span>
                      </div>
                    </div>
                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-green-500 to-emerald-500"
                        style={{ width: `${item.winRate}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Right Sidebar */}
          <div className="col-span-4 space-y-6">
            {/* Exposure Breakdown */}
            <Card className="bg-gradient-to-br from-slate-900/90 to-slate-950/90 border-slate-800/50 p-6">
              <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                <PieChart className="w-5 h-5" />
                Exposure by Stat
              </h2>

              <div className="h-48 mb-4">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsPieChart>
                    <Pie
                      data={exposureData}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={70}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {exposureData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1e293b",
                        border: "1px solid #334155",
                        borderRadius: "8px",
                      }}
                    />
                  </RechartsPieChart>
                </ResponsiveContainer>
              </div>

              <div className="space-y-2">
                {exposureData.map((item) => (
                  <div key={item.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="text-sm text-slate-400">{item.name}</span>
                    </div>
                    <span className="text-sm font-semibold text-white">
                      {item.value}%
                    </span>
                  </div>
                ))}
              </div>
            </Card>

            {/* Risk Metrics */}
            <Card className="bg-gradient-to-br from-slate-900/90 to-slate-950/90 border-slate-800/50 p-6">
              <h2 className="text-lg font-semibold text-white mb-6">Risk Metrics</h2>

              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-400">Max Drawdown</span>
                    <span className="text-sm font-semibold text-red-400">
                      {portfolioMetrics.maxDrawdown}%
                    </span>
                  </div>
                  <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-red-500"
                      style={{
                        width: `${Math.abs(portfolioMetrics.maxDrawdown) * 10}%`,
                      }}
                    />
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-slate-800/30 border border-slate-700/30">
                  <div className="text-xs text-slate-500 mb-1">
                    Portfolio Beta
                  </div>
                  <div className="text-lg font-semibold text-white">0.87</div>
                </div>

                <div className="p-3 rounded-lg bg-slate-800/30 border border-slate-700/30">
                  <div className="text-xs text-slate-500 mb-1">
                    Kelly Utilization
                  </div>
                  <div className="text-lg font-semibold text-white">42%</div>
                </div>

                <div className="p-3 rounded-lg bg-slate-800/30 border border-slate-700/30">
                  <div className="text-xs text-slate-500 mb-1">
                    Avg Hold Time
                  </div>
                  <div className="text-lg font-semibold text-white">2.4h</div>
                </div>
              </div>
            </Card>

            {/* Quick Actions */}
            <Card className="bg-gradient-to-br from-slate-900/90 to-slate-950/90 border-slate-800/50 p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>

              <div className="space-y-2">
                <Button
                  variant="outline"
                  className="w-full justify-start border-slate-700 hover:bg-slate-800"
                  onClick={() => navigate("/")}
                >
                  <TrendingUp className="w-4 h-4 mr-2" />
                  Find New Opportunities
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start border-slate-700 hover:bg-slate-800"
                >
                  <BarChart3 className="w-4 h-4 mr-2" />
                  View Analytics
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start border-slate-700 hover:bg-slate-800"
                >
                  <DollarSign className="w-4 h-4 mr-2" />
                  Export Report
                </Button>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
