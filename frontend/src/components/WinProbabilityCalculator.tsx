import { useEffect, useMemo, useState } from 'react'
import {
  getDynamicRange,
  getTeamBaselines,
  getTeamOddsBaselineProbability,
  getTeamStds,
  STAT_META,
  TEAM_OPTIONS,
  TEAM_RELATIVE_PRESETS,
  type StatInputs,
  type StatKey,
} from '../config/modelConfig'
import { calculateWinProbability } from '../utils/winProbability'

const statOrder: StatKey[] = ['points', 'rebounds', 'assists', 'fgPct', 'fg3Pct', 'turnovers']

function formatSigned(value: number): string {
  const rounded = value.toFixed(3)
  return value >= 0 ? `+${rounded}` : rounded
}

function formatStatValue(statKey: StatKey, value: number): string {
  if (STAT_META[statKey].asPercent) {
    return `${(value * 100).toFixed(1)}%`
  }
  return value.toFixed(0)
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}

function StatSlider({
  team,
  statKey,
  value,
  baseline,
  onChange,
}: {
  team: string
  statKey: StatKey
  value: number
  baseline: number
  onChange: (stat: StatKey, next: number) => void
}) {
  const meta = STAT_META[statKey]
  const range = getDynamicRange(team, statKey)

  return (
    <div className="rounded-xl border border-slate-600/50 bg-slate-900/45 p-4">
      <div className="mb-2 flex items-center justify-between">
        <label className="text-sm font-semibold text-slate-100">{meta.label}</label>
        <span className="text-sm font-mono text-cyan-300">{formatStatValue(statKey, value)}</span>
      </div>
      <input
        type="range"
        min={range.min}
        max={range.max}
        step={range.step}
        value={value}
        onChange={(e) => onChange(statKey, Number(e.target.value))}
        className="h-2 w-full cursor-pointer appearance-none rounded bg-slate-700 accent-cyan-400"
      />
      <div className="mt-2 flex justify-between text-xs text-slate-400">
        <span>{formatStatValue(statKey, range.min)}</span>
        <span>Team avg: {formatStatValue(statKey, baseline)}</span>
        <span>{formatStatValue(statKey, range.max)}</span>
      </div>
    </div>
  )
}

export default function WinProbabilityCalculator() {
  const [selectedTeam, setSelectedTeam] = useState<string>(TEAM_OPTIONS[0] ?? 'Boston Celtics')

  const baselines = useMemo(() => getTeamBaselines(selectedTeam), [selectedTeam])
  const teamStds = useMemo(() => getTeamStds(selectedTeam), [selectedTeam])
  const oddsBaselineProbability = useMemo(() => getTeamOddsBaselineProbability(selectedTeam), [selectedTeam])

  const [inputs, setInputs] = useState<StatInputs>(baselines)

  useEffect(() => {
    setInputs(baselines)
  }, [baselines])

  const result = useMemo(
    () => calculateWinProbability(inputs, baselines, teamStds, oddsBaselineProbability),
    [inputs, baselines, teamStds, oddsBaselineProbability],
  )

  const probabilityPct = Math.round(result.probability * 100)
  const probabilityColor =
    probabilityPct >= 65 ? 'text-emerald-300' : probabilityPct >= 45 ? 'text-amber-200' : 'text-rose-300'
  const progressColor = probabilityPct >= 65 ? 'bg-emerald-500' : probabilityPct >= 45 ? 'bg-amber-400' : 'bg-rose-500'

  const updateStat = (stat: StatKey, next: number) => {
    const range = getDynamicRange(selectedTeam, stat)
    const safe = clamp(next, range.min, range.max)
    setInputs((prev) => ({ ...prev, [stat]: safe }))
  }

  const applyPreset = (presetDeltas: StatInputs) => {
    const next: StatInputs = { ...baselines }
    statOrder.forEach((stat) => {
      const range = getDynamicRange(selectedTeam, stat)
      next[stat] = clamp(baselines[stat] + presetDeltas[stat], range.min, range.max)
    })
    setInputs(next)
  }

  const reset = () => {
    setInputs({ ...baselines })
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 text-slate-100 sm:px-6 lg:px-8">
      <header className="mb-8 rounded-2xl border border-slate-600/50 bg-slate-900/70 p-6 shadow-2xl shadow-black/20">
        <p className="mb-3 inline-flex rounded-full border border-amber-300/50 bg-amber-300/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-amber-200">
          Prototype v1.1: sensitivity-based estimate, not a full predictive model
        </p>
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">NBA Team Win Probability Sandbox</h1>
        <p className="mt-3 max-w-3xl text-sm text-slate-300 sm:text-base">
          This estimate starts from a team-specific baseline win probability derived from historical 2025 market odds,
          then moves up or down based on how your chosen stat line compares with that team&apos;s historical baseline stats.
        </p>
        <p className="mt-2 max-w-3xl text-xs text-slate-400 sm:text-sm">
          This is a sensitivity-based prototype, not yet a full opponent-aware predictive model.
        </p>
      </header>

      <section className="mb-8 grid gap-8 lg:grid-cols-[1.2fr_1fr]">
        <div className="space-y-4 rounded-2xl border border-slate-600/50 bg-slate-900/70 p-5 shadow-xl shadow-black/20">
          <div className="rounded-xl border border-slate-600/50 bg-slate-900/40 p-4">
            <label className="mb-2 block text-sm font-semibold text-slate-200">Selected Team</label>
            <select
              value={selectedTeam}
              onChange={(e) => setSelectedTeam(e.target.value)}
              className="w-full rounded-lg border border-slate-500 bg-slate-800 px-3 py-2 text-sm text-slate-100 outline-none ring-cyan-400 transition focus:ring-2"
            >
              {TEAM_OPTIONS.map((teamName) => (
                <option key={teamName} value={teamName}>
                  {teamName}
                </option>
              ))}
            </select>
          </div>

          <div className="mb-4 flex flex-wrap gap-2">
            {TEAM_RELATIVE_PRESETS.map((preset) => (
              <button
                key={preset.label}
                type="button"
                onClick={() => applyPreset(preset.deltas)}
                className="rounded-lg border border-slate-500 bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-100 transition hover:border-cyan-400 hover:text-cyan-200"
              >
                {preset.label}
              </button>
            ))}
            <button
              type="button"
              onClick={reset}
              className="rounded-lg border border-cyan-500 bg-cyan-500/10 px-3 py-1.5 text-xs font-semibold text-cyan-200 transition hover:bg-cyan-500/20"
            >
              Reset to Average
            </button>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            {statOrder.map((statKey) => (
              <StatSlider
                key={statKey}
                team={selectedTeam}
                statKey={statKey}
                value={inputs[statKey]}
                baseline={baselines[statKey]}
                onChange={updateStat}
              />
            ))}
          </div>
        </div>

        <div className="space-y-4 rounded-2xl border border-slate-600/50 bg-slate-900/70 p-6 shadow-xl shadow-black/20">
          <p className="text-sm uppercase tracking-wide text-slate-400">Estimated Win Probability</p>
          <div className={`text-5xl font-black ${probabilityColor}`}>{probabilityPct}%</div>
          <div className="h-4 w-full overflow-hidden rounded-full bg-slate-800">
            <div
              className={`h-full ${progressColor} transition-all duration-200`}
              style={{ width: `${probabilityPct}%` }}
            />
          </div>
          <p className="text-xs text-slate-400">
            {selectedTeam} odds baseline: {(result.baselineProbability * 100).toFixed(1)}%. Score adjustment:{' '}
            {result.score.toFixed(3)}
          </p>

          <div className="mt-4 rounded-xl border border-slate-600/50 bg-slate-950/40 p-4">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-300">Contribution Breakdown</h2>
            <ul className="space-y-2">
              {statOrder.map((statKey) => {
                const displayName = STAT_META[statKey].label
                const contribution = result.contributions[statKey]
                const z = result.zScores[statKey]
                return (
                  <li key={statKey} className="rounded-lg border border-slate-700/70 px-3 py-2 text-sm">
                    <div className="mb-1 flex items-center justify-between">
                      <span className="font-medium text-slate-200">{displayName}</span>
                      <span className={contribution >= 0 ? 'font-mono text-emerald-300' : 'font-mono text-rose-300'}>
                        {formatSigned(contribution)}
                      </span>
                    </div>
                    <div className="text-xs text-slate-400">
                      {formatStatValue(statKey, inputs[statKey])} vs team avg {formatStatValue(statKey, baselines[statKey])}
                      {' -> z = '}{formatSigned(z)}
                    </div>
                  </li>
                )
              })}
            </ul>
          </div>
        </div>
      </section>
    </main>
  )
}
