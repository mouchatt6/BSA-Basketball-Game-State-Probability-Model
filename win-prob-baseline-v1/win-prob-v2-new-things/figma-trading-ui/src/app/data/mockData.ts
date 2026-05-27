// Mock data for the prediction market arbitrage platform

export interface MarketOpportunity {
  id: string;
  gameId: string;
  player: string;
  team: string;
  opponent: string;
  statType: string;
  line: number;
  marketProb: number;
  modelProb: number;
  ev: number;
  kelly: number;
  liquidity: number;
  slippage: number;
  confidence: number;
  sharpMoney: "over" | "under" | "neutral";
  publicMoney: "over" | "under" | "neutral";
  lineMovement: number[];
  timestamp: Date;
  sportsbook: string;
}

export interface LiveGame {
  id: string;
  homeTeam: string;
  awayTeam: string;
  homeScore: number;
  awayScore: number;
  quarter: string;
  timeRemaining: string;
  status: "live" | "upcoming" | "final";
  startTime: Date;
}

export interface Position {
  id: string;
  player: string;
  statType: string;
  line: number;
  side: "over" | "under";
  stake: number;
  entryProb: number;
  currentProb: number;
  unrealizedPnL: number;
  expectedROI: number;
  timestamp: Date;
}

export const liveGames: LiveGame[] = [
  {
    id: "game-1",
    homeTeam: "GSW",
    awayTeam: "LAL",
    homeScore: 89,
    awayScore: 82,
    quarter: "Q3",
    timeRemaining: "7:34",
    status: "live",
    startTime: new Date("2026-05-26T19:30:00"),
  },
  {
    id: "game-2",
    homeTeam: "BOS",
    awayTeam: "MIA",
    homeScore: 54,
    awayScore: 51,
    quarter: "Q2",
    timeRemaining: "2:18",
    status: "live",
    startTime: new Date("2026-05-26T19:00:00"),
  },
  {
    id: "game-3",
    homeTeam: "DAL",
    awayTeam: "PHX",
    homeScore: 0,
    awayScore: 0,
    quarter: "",
    timeRemaining: "",
    status: "upcoming",
    startTime: new Date("2026-05-26T21:30:00"),
  },
  {
    id: "game-4",
    homeTeam: "DEN",
    awayTeam: "LAC",
    homeScore: 0,
    awayScore: 0,
    quarter: "",
    timeRemaining: "",
    status: "upcoming",
    startTime: new Date("2026-05-26T22:00:00"),
  },
];

export const marketOpportunities: MarketOpportunity[] = [
  {
    id: "market-1",
    gameId: "game-1",
    player: "Stephen Curry",
    team: "GSW",
    opponent: "LAL",
    statType: "Points",
    line: 29.5,
    marketProb: 43,
    modelProb: 58,
    ev: 15.2,
    kelly: 8.5,
    liquidity: 125000,
    slippage: 0.3,
    confidence: 87,
    sharpMoney: "over",
    publicMoney: "under",
    lineMovement: [42, 41.5, 43, 44, 43],
    timestamp: new Date(),
    sportsbook: "Polymarket",
  },
  {
    id: "market-2",
    gameId: "game-1",
    player: "LeBron James",
    team: "LAL",
    opponent: "GSW",
    statType: "Rebounds",
    line: 8.5,
    marketProb: 61,
    modelProb: 48,
    ev: -13.1,
    kelly: 0,
    liquidity: 89000,
    slippage: 0.5,
    confidence: 72,
    sharpMoney: "under",
    publicMoney: "over",
    lineMovement: [58, 59, 61, 62, 61],
    timestamp: new Date(),
    sportsbook: "Kalshi",
  },
  {
    id: "market-3",
    gameId: "game-2",
    player: "Jayson Tatum",
    team: "BOS",
    opponent: "MIA",
    statType: "Points",
    line: 27.5,
    marketProb: 52,
    modelProb: 64,
    ev: 12.4,
    kelly: 6.8,
    liquidity: 156000,
    slippage: 0.2,
    confidence: 91,
    sharpMoney: "over",
    publicMoney: "over",
    lineMovement: [49, 50, 51, 52, 52],
    timestamp: new Date(),
    sportsbook: "Polymarket",
  },
  {
    id: "market-4",
    gameId: "game-2",
    player: "Jimmy Butler",
    team: "MIA",
    opponent: "BOS",
    statType: "Assists",
    line: 5.5,
    marketProb: 46,
    modelProb: 59,
    ev: 13.8,
    kelly: 7.2,
    liquidity: 72000,
    slippage: 0.6,
    confidence: 84,
    sharpMoney: "over",
    publicMoney: "neutral",
    lineMovement: [44, 45, 46, 47, 46],
    timestamp: new Date(),
    sportsbook: "Kalshi",
  },
  {
    id: "market-5",
    gameId: "game-3",
    player: "Luka Dončić",
    team: "DAL",
    opponent: "PHX",
    statType: "Points",
    line: 32.5,
    marketProb: 48,
    modelProb: 67,
    ev: 19.3,
    kelly: 11.2,
    liquidity: 203000,
    slippage: 0.15,
    confidence: 93,
    sharpMoney: "over",
    publicMoney: "under",
    lineMovement: [45, 46, 47, 48, 48],
    timestamp: new Date(),
    sportsbook: "Polymarket",
  },
  {
    id: "market-6",
    gameId: "game-3",
    player: "Devin Booker",
    team: "PHX",
    opponent: "DAL",
    statType: "Points",
    line: 28.5,
    marketProb: 55,
    modelProb: 51,
    ev: -4.2,
    kelly: 0,
    liquidity: 98000,
    slippage: 0.4,
    confidence: 68,
    sharpMoney: "under",
    publicMoney: "over",
    lineMovement: [53, 54, 55, 56, 55],
    timestamp: new Date(),
    sportsbook: "Kalshi",
  },
  {
    id: "market-7",
    gameId: "game-1",
    player: "Anthony Davis",
    team: "LAL",
    opponent: "GSW",
    statType: "Points + Rebounds",
    line: 38.5,
    marketProb: 49,
    modelProb: 63,
    ev: 14.7,
    kelly: 8.1,
    liquidity: 134000,
    slippage: 0.25,
    confidence: 89,
    sharpMoney: "over",
    publicMoney: "neutral",
    lineMovement: [47, 48, 49, 49, 49],
    timestamp: new Date(),
    sportsbook: "Polymarket",
  },
  {
    id: "market-8",
    gameId: "game-4",
    player: "Nikola Jokić",
    team: "DEN",
    opponent: "LAC",
    statType: "Triple-Double",
    line: 0.5,
    marketProb: 24,
    modelProb: 38,
    ev: 14.1,
    kelly: 9.3,
    liquidity: 45000,
    slippage: 0.8,
    confidence: 76,
    sharpMoney: "over",
    publicMoney: "under",
    lineMovement: [22, 23, 24, 25, 24],
    timestamp: new Date(),
    sportsbook: "Kalshi",
  },
];

export const positions: Position[] = [
  {
    id: "pos-1",
    player: "Damian Lillard",
    statType: "Points",
    line: 26.5,
    side: "over",
    stake: 850,
    entryProb: 47,
    currentProb: 52,
    unrealizedPnL: 127,
    expectedROI: 14.9,
    timestamp: new Date("2026-05-26T17:45:00"),
  },
  {
    id: "pos-2",
    player: "Joel Embiid",
    statType: "Rebounds",
    line: 11.5,
    side: "over",
    stake: 1200,
    entryProb: 55,
    currentProb: 49,
    unrealizedPnL: -84,
    expectedROI: -7.0,
    timestamp: new Date("2026-05-26T18:12:00"),
  },
  {
    id: "pos-3",
    player: "Giannis Antetokounmpo",
    statType: "Points + Rebounds",
    line: 42.5,
    side: "over",
    stake: 1500,
    entryProb: 51,
    currentProb: 58,
    unrealizedPnL: 243,
    expectedROI: 16.2,
    timestamp: new Date("2026-05-26T16:30:00"),
  },
];

export const portfolioMetrics = {
  totalValue: 3550,
  unrealizedPnL: 286,
  realizedPnL: 1847,
  winRate: 64.2,
  avgEV: 11.3,
  sharpeRatio: 2.14,
  maxDrawdown: -8.7,
  totalTrades: 127,
};
