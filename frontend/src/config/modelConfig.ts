export type StatKey = 'points' | 'rebounds' | 'assists' | 'fgPct' | 'fg3Pct' | 'turnovers'

export type StatInputs = Record<StatKey, number>

export type TeamStatsMap = Record<string, StatInputs>

export const STAT_META: Record<StatKey, { label: string; step: number; asPercent?: boolean }> = {
  points: { label: 'Points', step: 1 },
  rebounds: { label: 'Rebounds', step: 1 },
  assists: { label: 'Assists', step: 1 },
  fgPct: { label: 'FG%', step: 0.001, asPercent: true },
  fg3Pct: { label: '3PT%', step: 0.001, asPercent: true },
  turnovers: { label: 'Turnovers', step: 1 },
}

// Team-level historical baselines from team_game_dataset.csv (2016-17 to 2023-24)
// TODO: replace with automated export from data pipeline in future iterations.
export const TEAM_BASELINES: TeamStatsMap = {
  'Atlanta Hawks': { points: 111.979, rebounds: 44.282, assists: 24.707, fgPct: 0.462, fg3Pct: 0.356, turnovers: 13.933 },
  'Boston Celtics': { points: 112.604, rebounds: 44.868, assists: 24.904, fgPct: 0.467, fg3Pct: 0.37, turnovers: 12.728 },
  'Brooklyn Nets': { points: 111.33, rebounds: 44.475, assists: 24.539, fgPct: 0.463, fg3Pct: 0.36, turnovers: 13.833 },
  'Charlotte Hornets': { points: 108.774, rebounds: 43.618, assists: 24.555, fgPct: 0.453, fg3Pct: 0.353, turnovers: 12.747 },
  'Chicago Bulls': { points: 108.153, rebounds: 43.672, assists: 23.878, fgPct: 0.463, fg3Pct: 0.354, turnovers: 13.116 },
  'Cleveland Cavaliers': { points: 108.76, rebounds: 42.981, assists: 24, fgPct: 0.468, fg3Pct: 0.36, turnovers: 13.39 },
  'Dallas Mavericks': { points: 109.712, rebounds: 42.46, assists: 23.288, fgPct: 0.461, fg3Pct: 0.359, turnovers: 11.959 },
  'Denver Nuggets': { points: 112.747, rebounds: 44.689, assists: 27.203, fgPct: 0.482, fg3Pct: 0.365, turnovers: 13.386 },
  'Detroit Pistons': { points: 106.351, rebounds: 43.502, assists: 23.29, fgPct: 0.45, fg3Pct: 0.348, turnovers: 13.503 },
  'Golden State Warriors': { points: 114.576, rebounds: 44.671, assists: 28.666, fgPct: 0.479, fg3Pct: 0.375, turnovers: 14.48 },
  'Houston Rockets': { points: 112.862, rebounds: 43.827, assists: 23.013, fgPct: 0.456, fg3Pct: 0.348, turnovers: 14 },
  'Indiana Pacers': { points: 111.785, rebounds: 42.463, assists: 25.852, fgPct: 0.476, fg3Pct: 0.365, turnovers: 13.133 },
  'LA Clippers': { points: 112.517, rebounds: 44.25, assists: 23.803, fgPct: 0.475, fg3Pct: 0.378, turnovers: 13.179 },
  'Los Angeles Lakers': { points: 111.846, rebounds: 44.906, assists: 24.754, fgPct: 0.473, fg3Pct: 0.348, turnovers: 14.392 },
  'Memphis Grizzlies': { points: 108.316, rebounds: 44.502, assists: 24.597, fgPct: 0.455, fg3Pct: 0.349, turnovers: 13.361 },
  'Miami Heat': { points: 107.691, rebounds: 43.25, assists: 24.4, fgPct: 0.462, fg3Pct: 0.363, turnovers: 13.226 },
  'Milwaukee Bucks': { points: 114.664, rebounds: 46.053, assists: 25.116, fgPct: 0.478, fg3Pct: 0.366, turnovers: 13.33 },
  'Minnesota Timberwolves': { points: 112.175, rebounds: 43.354, assists: 24.881, fgPct: 0.467, fg3Pct: 0.358, turnovers: 13.457 },
  'New Orleans Pelicans': { points: 112.502, rebounds: 45.206, assists: 25.885, fgPct: 0.473, fg3Pct: 0.355, turnovers: 13.811 },
  'New York Knicks': { points: 107.746, rebounds: 45.414, assists: 22.241, fgPct: 0.453, fg3Pct: 0.356, turnovers: 12.925 },
  'Oklahoma City Thunder': { points: 110.799, rebounds: 44.965, assists: 22.932, fgPct: 0.459, fg3Pct: 0.349, turnovers: 13.434 },
  'Orlando Magic': { points: 106.165, rebounds: 43.714, assists: 23.595, fgPct: 0.451, fg3Pct: 0.343, turnovers: 13.254 },
  'Philadelphia 76ers': { points: 111.421, rebounds: 44.314, assists: 25.143, fgPct: 0.469, fg3Pct: 0.364, turnovers: 13.673 },
  'Phoenix Suns': { points: 111.505, rebounds: 43.708, assists: 25.003, fgPct: 0.47, fg3Pct: 0.355, turnovers: 13.856 },
  'Portland Trail Blazers': { points: 110.524, rebounds: 44.119, assists: 21.991, fgPct: 0.457, fg3Pct: 0.364, turnovers: 13.094 },
  'Sacramento Kings': { points: 110.871, rebounds: 42.615, assists: 24.761, fgPct: 0.469, fg3Pct: 0.368, turnovers: 13.25 },
  'San Antonio Spurs': { points: 110.32, rebounds: 44.324, assists: 25.693, fgPct: 0.468, fg3Pct: 0.364, turnovers: 12.819 },
  'Toronto Raptors': { points: 111.428, rebounds: 43.813, assists: 23.983, fgPct: 0.463, fg3Pct: 0.357, turnovers: 12.566 },
  'Utah Jazz': { points: 111.248, rebounds: 45.423, assists: 23.802, fgPct: 0.469, fg3Pct: 0.365, turnovers: 14.107 },
  'Washington Wizards': { points: 111.94, rebounds: 42.901, assists: 25.525, fgPct: 0.472, fg3Pct: 0.356, turnovers: 13.514 },
}

export const TEAM_STDS: TeamStatsMap = {
  'Atlanta Hawks': { points: 13.328, rebounds: 6.721, assists: 4.623, fgPct: 0.055, fg3Pct: 0.082, turnovers: 3.952 },
  'Boston Celtics': { points: 12.682, rebounds: 6.41, assists: 5.07, fgPct: 0.054, fg3Pct: 0.082, turnovers: 3.525 },
  'Brooklyn Nets': { points: 12.51, rebounds: 6.805, assists: 4.834, fgPct: 0.057, fg3Pct: 0.083, turnovers: 3.854 },
  'Charlotte Hornets': { points: 12.448, rebounds: 6.602, assists: 4.886, fgPct: 0.055, fg3Pct: 0.088, turnovers: 3.933 },
  'Chicago Bulls': { points: 12.591, rebounds: 6.453, assists: 4.858, fgPct: 0.057, fg3Pct: 0.091, turnovers: 3.995 },
  'Cleveland Cavaliers': { points: 12.075, rebounds: 6.356, assists: 5.286, fgPct: 0.054, fg3Pct: 0.086, turnovers: 3.812 },
  'Dallas Mavericks': { points: 13.531, rebounds: 6.597, assists: 4.705, fgPct: 0.054, fg3Pct: 0.08, turnovers: 3.66 },
  'Denver Nuggets': { points: 12.268, rebounds: 6.302, assists: 5.213, fgPct: 0.059, fg3Pct: 0.089, turnovers: 3.888 },
  'Detroit Pistons': { points: 12.038, rebounds: 6.532, assists: 4.558, fgPct: 0.051, fg3Pct: 0.087, turnovers: 3.911 },
  'Golden State Warriors': { points: 13.062, rebounds: 6.407, assists: 5.534, fgPct: 0.057, fg3Pct: 0.089, turnovers: 3.709 },
  'Houston Rockets': { points: 12.712, rebounds: 6.628, assists: 4.842, fgPct: 0.053, fg3Pct: 0.076, turnovers: 3.966 },
  'Indiana Pacers': { points: 13.226, rebounds: 6.272, assists: 5.517, fgPct: 0.057, fg3Pct: 0.093, turnovers: 3.678 },
  'LA Clippers': { points: 13.131, rebounds: 6.427, assists: 4.962, fgPct: 0.057, fg3Pct: 0.092, turnovers: 3.895 },
  'Los Angeles Lakers': { points: 12.461, rebounds: 6.415, assists: 5.043, fgPct: 0.05, fg3Pct: 0.088, turnovers: 4.04 },
  'Memphis Grizzlies': { points: 13.248, rebounds: 7.167, assists: 5.081, fgPct: 0.053, fg3Pct: 0.089, turnovers: 3.752 },
  'Miami Heat': { points: 11.782, rebounds: 6.597, assists: 4.847, fgPct: 0.052, fg3Pct: 0.083, turnovers: 3.884 },
  'Milwaukee Bucks': { points: 13.62, rebounds: 7.423, assists: 4.848, fgPct: 0.054, fg3Pct: 0.082, turnovers: 3.512 },
  'Minnesota Timberwolves': { points: 11.678, rebounds: 6.571, assists: 4.843, fgPct: 0.052, fg3Pct: 0.084, turnovers: 3.637 },
  'New Orleans Pelicans': { points: 12.152, rebounds: 6.569, assists: 4.976, fgPct: 0.052, fg3Pct: 0.09, turnovers: 3.848 },
  'New York Knicks': { points: 12.176, rebounds: 6.508, assists: 4.526, fgPct: 0.052, fg3Pct: 0.089, turnovers: 3.676 },
  'Oklahoma City Thunder': { points: 13.05, rebounds: 6.484, assists: 5.238, fgPct: 0.056, fg3Pct: 0.087, turnovers: 3.718 },
  'Orlando Magic': { points: 12.326, rebounds: 5.951, assists: 4.801, fgPct: 0.055, fg3Pct: 0.086, turnovers: 3.549 },
  'Philadelphia 76ers': { points: 12.421, rebounds: 6.625, assists: 5.02, fgPct: 0.053, fg3Pct: 0.085, turnovers: 4.205 },
  'Phoenix Suns': { points: 11.905, rebounds: 6.627, assists: 5.474, fgPct: 0.055, fg3Pct: 0.087, turnovers: 3.965 },
  'Portland Trail Blazers': { points: 12.786, rebounds: 6.856, assists: 4.73, fgPct: 0.055, fg3Pct: 0.086, turnovers: 3.805 },
  'Sacramento Kings': { points: 13.512, rebounds: 6.457, assists: 4.926, fgPct: 0.053, fg3Pct: 0.084, turnovers: 3.67 },
  'San Antonio Spurs': { points: 12.568, rebounds: 5.975, assists: 5.302, fgPct: 0.053, fg3Pct: 0.095, turnovers: 3.76 },
  'Toronto Raptors': { points: 11.848, rebounds: 6.119, assists: 5.602, fgPct: 0.055, fg3Pct: 0.087, turnovers: 3.647 },
  'Utah Jazz': { points: 12.978, rebounds: 6.621, assists: 5.301, fgPct: 0.054, fg3Pct: 0.082, turnovers: 3.779 },
  'Washington Wizards': { points: 12.261, rebounds: 6.219, assists: 4.976, fgPct: 0.053, fg3Pct: 0.09, turnovers: 3.809 },
}

// Baseline pregame win probabilities for 2025 derived from nba_2008-2025.csv.
// Because 2025 moneylines are missing in the file, these are inferred from spreads:
// (1) fit logistic win~signed_spread on historical seasons, then
// (2) apply to 2025 spreads and average by team.
export const TEAM_ODDS_BASELINE_PROB: Record<string, number> = {
  'Atlanta Hawks': 0.4616,
  'Boston Celtics': 0.7721,
  'Brooklyn Nets': 0.2852,
  'Charlotte Hornets': 0.2808,
  'Chicago Bulls': 0.3918,
  'Cleveland Cavaliers': 0.7265,
  'Dallas Mavericks': 0.477,
  'Denver Nuggets': 0.6191,
  'Detroit Pistons': 0.4899,
  'Golden State Warriors': 0.6087,
  'Houston Rockets': 0.5892,
  'Indiana Pacers': 0.5728,
  'LA Clippers': 0.5671,
  'Los Angeles Lakers': 0.5466,
  'Memphis Grizzlies': 0.5658,
  'Miami Heat': 0.5191,
  'Milwaukee Bucks': 0.5758,
  'Minnesota Timberwolves': 0.6329,
  'New Orleans Pelicans': 0.3405,
  'New York Knicks': 0.6519,
  'Oklahoma City Thunder': 0.7602,
  'Orlando Magic': 0.5254,
  'Philadelphia 76ers': 0.4044,
  'Phoenix Suns': 0.5117,
  'Portland Trail Blazers': 0.3418,
  'Sacramento Kings': 0.5784,
  'San Antonio Spurs': 0.4129,
  'Toronto Raptors': 0.3305,
  'Utah Jazz': 0.2459,
  'Washington Wizards': 0.2143,
}

export const LEAGUE_STDS: StatInputs = {
  points: 12.796,
  rebounds: 6.587,
  assists: 5.195,
  fgPct: 0.055,
  fg3Pct: 0.087,
  turnovers: 3.839,
}

// Basketball-informed v1.1 prototype weights
// Replace with fitted model importances in future versions.
export const WEIGHTS: StatInputs = {
  points: 0.24,
  rebounds: 0.14,
  assists: 0.16,
  fgPct: 0.24,
  fg3Pct: 0.1,
  turnovers: 0.2,
}

export const SIGMOID_K = 0.9

export const TEAM_OPTIONS = Object.keys(TEAM_BASELINES).sort()

const sliderOffsets: StatInputs = {
  points: 20,
  rebounds: 15,
  assists: 12,
  fgPct: 0.15,
  fg3Pct: 0.15,
  turnovers: 8,
}

const sliderBounds: Record<StatKey, { min: number; max: number }> = {
  points: { min: 70, max: 150 },
  rebounds: { min: 20, max: 75 },
  assists: { min: 8, max: 45 },
  fgPct: { min: 0.25, max: 0.75 },
  fg3Pct: { min: 0.15, max: 0.65 },
  turnovers: { min: 3, max: 30 },
}

export function getTeamBaselines(team: string): StatInputs {
  return TEAM_BASELINES[team] ?? TEAM_BASELINES[TEAM_OPTIONS[0]]
}

export function getTeamStds(team: string): StatInputs {
  const teamStds = TEAM_STDS[team] ?? LEAGUE_STDS
  return {
    points: teamStds.points > 0.01 ? teamStds.points : LEAGUE_STDS.points,
    rebounds: teamStds.rebounds > 0.01 ? teamStds.rebounds : LEAGUE_STDS.rebounds,
    assists: teamStds.assists > 0.01 ? teamStds.assists : LEAGUE_STDS.assists,
    fgPct: teamStds.fgPct > 0.0001 ? teamStds.fgPct : LEAGUE_STDS.fgPct,
    fg3Pct: teamStds.fg3Pct > 0.0001 ? teamStds.fg3Pct : LEAGUE_STDS.fg3Pct,
    turnovers: teamStds.turnovers > 0.01 ? teamStds.turnovers : LEAGUE_STDS.turnovers,
  }
}

export function getTeamOddsBaselineProbability(team: string): number {
  return TEAM_ODDS_BASELINE_PROB[team] ?? 0.5
}

export function getDynamicRange(team: string, statKey: StatKey) {
  const baseline = getTeamBaselines(team)[statKey]
  const offset = sliderOffsets[statKey]
  const bounds = sliderBounds[statKey]
  return {
    min: Math.max(bounds.min, baseline - offset),
    max: Math.min(bounds.max, baseline + offset),
    step: STAT_META[statKey].step,
  }
}

type TeamPreset = {
  label: string
  deltas: StatInputs
}

export const TEAM_RELATIVE_PRESETS: TeamPreset[] = [
  {
    label: 'Strong Offensive Night',
    deltas: { points: 8, rebounds: 2, assists: 4, fgPct: 0.05, fg3Pct: 0.03, turnovers: 1 },
  },
  {
    label: 'Efficient Shooting Night',
    deltas: { points: 6, rebounds: 1, assists: 2, fgPct: 0.08, fg3Pct: 0.05, turnovers: -1 },
  },
  {
    label: 'Sloppy Night',
    deltas: { points: -7, rebounds: -2, assists: -3, fgPct: -0.05, fg3Pct: -0.04, turnovers: 4 },
  },
  {
    label: 'Glass Control Night',
    deltas: { points: 3, rebounds: 8, assists: 1, fgPct: 0.01, fg3Pct: 0, turnovers: -1 },
  },
]
