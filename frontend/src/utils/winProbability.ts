import { SIGMOID_K, type StatInputs, WEIGHTS } from '../config/modelConfig'

export type ProbabilityResult = {
  score: number
  probability: number
  contributions: StatInputs
  zScores: StatInputs
  baselineProbability: number
}

const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value))
const sigmoid = (x: number) => 1 / (1 + Math.exp(-x))
const logit = (p: number) => Math.log(p / (1 - p))

export function calculateWinProbability(
  inputs: StatInputs,
  baselines: StatInputs,
  stds: StatInputs,
  baselineProbability: number,
): ProbabilityResult {
  // Portable prototype logic:
  // 1) Standardize selected statline vs selected team's historical baseline.
  // 2) Build weighted score from those z-values.
  // 3) Shift team-specific baseline odds probability in log-odds space.
  const zScores: StatInputs = {
    points: (inputs.points - baselines.points) / stds.points,
    rebounds: (inputs.rebounds - baselines.rebounds) / stds.rebounds,
    assists: (inputs.assists - baselines.assists) / stds.assists,
    fgPct: (inputs.fgPct - baselines.fgPct) / stds.fgPct,
    fg3Pct: (inputs.fg3Pct - baselines.fg3Pct) / stds.fg3Pct,
    turnovers: (inputs.turnovers - baselines.turnovers) / stds.turnovers,
  }

  const contributions: StatInputs = {
    points: WEIGHTS.points * zScores.points,
    rebounds: WEIGHTS.rebounds * zScores.rebounds,
    assists: WEIGHTS.assists * zScores.assists,
    fgPct: WEIGHTS.fgPct * zScores.fgPct,
    fg3Pct: WEIGHTS.fg3Pct * zScores.fg3Pct,
    turnovers: -WEIGHTS.turnovers * zScores.turnovers,
  }

  const score = Object.values(contributions).reduce((total, item) => total + item, 0)
  const safeBaseline = clamp(baselineProbability, 0.01, 0.99)
  const anchoredLogit = logit(safeBaseline) + SIGMOID_K * score
  const probability = clamp(sigmoid(anchoredLogit), 0.01, 0.99)

  return {
    score,
    probability,
    contributions,
    zScores,
    baselineProbability: safeBaseline,
  }
}
