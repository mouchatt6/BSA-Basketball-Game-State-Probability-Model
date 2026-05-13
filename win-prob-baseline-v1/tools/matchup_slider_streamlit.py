from __future__ import annotations

import json
import math
from pathlib import Path
import time

import pandas as pd
import streamlit as st
from nba_api.stats.endpoints import leaguegamefinder


def logistic(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def to_nba_abbr(abbr: str) -> str:
    txt = str(abbr).strip().lower()
    custom = {
        "gs": "GSW",
        "sa": "SAS",
        "ny": "NYK",
        "no": "NOP",
        "phx": "PHX",
    }
    return custom.get(txt, txt.upper())


def infer_position(avg_ast: float, avg_reb: float) -> str:
    if avg_ast >= 5.5 and avg_reb <= 6.5:
        return "G"
    if avg_reb >= 7.5 and avg_ast <= 4.5:
        return "C"
    return "F"


@st.cache_data(show_spinner=False)
def load_matchups(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df[(df["season"] == 2025) & (df["regular"] == True)].copy()
    df = df.sort_values("date").reset_index(drop=True)
    if df.empty:
        raise RuntimeError("No 2025 regular season games found.")
    return df


@st.cache_data(show_spinner=True)
def load_player_logs_2024_25(cache_path: Path) -> pd.DataFrame:
    logs = None
    if cache_path.exists():
        logs = pd.read_csv(cache_path)
    else:
        last_error = None
        for attempt in range(1, 4):
            try:
                finder = leaguegamefinder.LeagueGameFinder(
                    season_nullable="2024-25",
                    season_type_nullable="Regular Season",
                    player_or_team_abbreviation="P",
                    league_id_nullable="00",
                    timeout=90,
                )
                logs = finder.get_data_frames()[0].copy()
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                logs.to_csv(cache_path, index=False)
                break
            except Exception as exc:
                last_error = exc
                time.sleep(1.0 * attempt)

        if logs is None:
            fallback = cache_path.parent / "player_game_logs_2023-24.csv"
            if fallback.exists():
                st.warning("Could not fetch 2024-25 player logs live; using cached 2023-24 player logs.")
                logs = pd.read_csv(fallback)
            else:
                raise RuntimeError("Unable to load player logs for slider app.") from last_error

    logs["GAME_DATE"] = pd.to_datetime(logs["GAME_DATE"], errors="coerce").dt.date
    logs["MIN"] = pd.to_numeric(logs["MIN"], errors="coerce").fillna(0.0)
    logs["PTS"] = pd.to_numeric(logs["PTS"], errors="coerce").fillna(0.0)
    logs["REB"] = pd.to_numeric(logs["REB"], errors="coerce").fillna(0.0)
    logs["AST"] = pd.to_numeric(logs["AST"], errors="coerce").fillna(0.0)
    logs["PLAYER_ID"] = pd.to_numeric(logs["PLAYER_ID"], errors="coerce")
    return logs.dropna(subset=["GAME_DATE", "PLAYER_ID"]).copy()


def build_player_pool_for_game(row: pd.Series, logs: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    game_date = pd.to_datetime(row["date"], errors="coerce").date()
    away_abbr = to_nba_abbr(row["away"])
    home_abbr = to_nba_abbr(row["home"])

    same_day = logs[logs["GAME_DATE"] == game_date].copy()
    away_day = same_day[same_day["TEAM_ABBREVIATION"] == away_abbr].copy()
    home_day = same_day[same_day["TEAM_ABBREVIATION"] == home_abbr].copy()
    game_ids = set(away_day["GAME_ID"]).intersection(set(home_day["GAME_ID"]))
    game_logs: pd.DataFrame
    if game_ids:
        game_id = sorted(game_ids)[0]
        game_logs = same_day[same_day["GAME_ID"] == game_id].copy()
    else:
        # Fallback: use top-minute players for each team across loaded season.
        game_logs = logs[logs["TEAM_ABBREVIATION"].isin([away_abbr, home_abbr])].copy()

    season_profile = (
        logs.groupby(["PLAYER_ID", "PLAYER_NAME"], as_index=False)
        .agg(avg_ast=("AST", "mean"), avg_reb=("REB", "mean"))
        .copy()
    )
    season_profile["position"] = season_profile.apply(
        lambda r: infer_position(float(r["avg_ast"]), float(r["avg_reb"])),
        axis=1,
    )
    pos_map = season_profile.set_index("PLAYER_ID")["position"].to_dict()

    def top_five(team_abbr: str, actual_game_mode: bool) -> pd.DataFrame:
        team = game_logs[game_logs["TEAM_ABBREVIATION"] == team_abbr].copy()
        if actual_game_mode:
            team = team.sort_values("MIN", ascending=False).head(5).copy()
        else:
            team = (
                team.groupby(["PLAYER_ID", "PLAYER_NAME", "TEAM_ABBREVIATION"], as_index=False)
                .agg(MIN=("MIN", "mean"), PTS=("PTS", "mean"), REB=("REB", "mean"), AST=("AST", "mean"))
                .sort_values("MIN", ascending=False)
                .head(5)
                .copy()
            )
        team["position"] = team["PLAYER_ID"].map(pos_map).fillna("F")
        prefix = "Actual" if actual_game_mode else "SeasonAvg"
        team["label"] = team.apply(lambda r: f"{r['PLAYER_NAME']} ({r['position']}) | {prefix} {int(r['PTS'])}/{int(r['REB'])}/{int(r['AST'])}", axis=1)
        return team

    actual_mode = bool(game_ids)
    return top_five(home_abbr, actual_mode), top_five(away_abbr, actual_mode)


def signed_spread_home(row: pd.Series) -> float:
    return float(row["spread"]) if str(row["whos_favored"]).lower() == "home" else -float(row["spread"])


def main() -> None:
    st.set_page_config(page_title="Matchup Slider Test", layout="wide")
    st.title("Win Prob V1 - Matchup Slider Test")

    project_root = Path(__file__).resolve().parents[1]
    model = json.loads((project_root / "outputs" / "baseline_params.json").read_text())
    weights = json.loads((project_root / "outputs" / "position_stat_weights.json").read_text())
    matchup_df = load_matchups(project_root.parent / "nba_2008-2025.csv")
    player_logs = load_player_logs_2024_25(project_root / "data" / "player_game_logs_2024-25.csv")

    options = [
        f"{r.date} | {str(r.away).upper()} @ {str(r.home).upper()} | spread {r.spread} ({r.whos_favored})"
        for r in matchup_df.itertuples(index=False)
    ]
    selected = st.selectbox("Select matchup", options=options, index=0)
    row = matchup_df.iloc[options.index(selected)]

    home_win_actual = int(row["score_home"] > row["score_away"])
    s0 = signed_spread_home(row)
    p0 = logistic(float(model["intercept"]) + float(model["spread_coef"]) * s0)
    home_players, away_players = build_player_pool_for_game(row=row, logs=player_logs)

    if home_players.empty or away_players.empty:
        st.error("Could not locate player game logs for this matchup/date.")
        st.stop()

    delta_margin = 0.0

    base = weights["stat_coefficients"]
    mult = weights["position_multipliers"]
    st.markdown("### Win Probability Meter")

    placeholder_meter = st.empty()
    placeholder_meta = st.empty()

    st.markdown("### Actual Players - Slider Deltas (PTS/REB/AST)")
    col_home, col_away = st.columns(2)
    with col_home:
        st.markdown(f"**Home: {to_nba_abbr(row['home'])} (Top 5 by minutes)**")
        for i, p in enumerate(home_players.itertuples(index=False), start=1):
            pos = str(p.position)
            st.markdown(f"`{p.label}`")
            c1, c2, c3 = st.columns(3)
            uid = f"{row['date']}_{row['home']}_{row['away']}_h_{int(p.PLAYER_ID)}"
            d_pts = c1.slider(f"H{i} PTS", -12, 12, 0, 1, key=f"{uid}_pts")
            d_reb = c2.slider(f"H{i} REB", -12, 12, 0, 1, key=f"{uid}_reb")
            d_ast = c3.slider(f"H{i} AST", -12, 12, 0, 1, key=f"{uid}_ast")
            delta_margin += (
                float(base["points"]) * float(mult[pos]["points"]) * d_pts
                + float(base["rebounds"]) * float(mult[pos]["rebounds"]) * d_reb
                + float(base["assists"]) * float(mult[pos]["assists"]) * d_ast
            )

    with col_away:
        st.markdown(f"**Away: {to_nba_abbr(row['away'])} (Top 5 by minutes)**")
        for i, p in enumerate(away_players.itertuples(index=False), start=1):
            pos = str(p.position)
            st.markdown(f"`{p.label}`")
            c1, c2, c3 = st.columns(3)
            uid = f"{row['date']}_{row['home']}_{row['away']}_a_{int(p.PLAYER_ID)}"
            d_pts = c1.slider(f"A{i} PTS", -12, 12, 0, 1, key=f"{uid}_pts")
            d_reb = c2.slider(f"A{i} REB", -12, 12, 0, 1, key=f"{uid}_reb")
            d_ast = c3.slider(f"A{i} AST", -12, 12, 0, 1, key=f"{uid}_ast")
            delta_margin -= (
                float(base["points"]) * float(mult[pos]["points"]) * d_pts
                + float(base["rebounds"]) * float(mult[pos]["rebounds"]) * d_reb
                + float(base["assists"]) * float(mult[pos]["assists"]) * d_ast
            )

    s1 = s0 + delta_margin
    p1 = logistic(float(model["intercept"]) + float(model["spread_coef"]) * s1)
    placeholder_meter.progress(int(round(p1 * 100)), text=f"Adjusted Home Win Probability: {p1 * 100:.1f}%")
    placeholder_meta.caption(
        f"Baseline: {p0 * 100:.1f}% | Spread(home signed): {s0:+.1f} | "
        f"Actual final: {int(row['score_away'])}-{int(row['score_home'])} "
        f"({'HOME WIN' if home_win_actual else 'AWAY WIN'})"
    )

    st.markdown("### Output")
    c1, c2, c3 = st.columns(3)
    c1.metric("Baseline P(home)", f"{p0:.3f}")
    c2.metric("Adjusted P(home)", f"{p1:.3f}")
    c3.metric("Delta margin", f"{delta_margin:+.2f}")

    pred_base = "HOME" if p0 >= 0.5 else "AWAY"
    pred_adj = "HOME" if p1 >= 0.5 else "AWAY"
    st.write(
        f"Predicted winner baseline/adjusted: **{pred_base} / {pred_adj}** | "
        f"Actual: **{'HOME' if home_win_actual else 'AWAY'}**"
    )

    st.markdown("### Learned Weights Used")
    st.json(weights)


if __name__ == "__main__":
    main()
