import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from nba_api.stats.endpoints import leaguegamefinder
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

sns.set_theme(style="whitegrid")

SEASONS = [
    "2016-17",
    "2017-18",
    "2018-19",
    "2019-20",
    "2020-21",
    "2021-22",
    "2022-23",
    "2023-24",
]

CORE_TEAM_COLS = [
    "SEASON_ID",
    "TEAM_ID",
    "TEAM_NAME",
    "GAME_ID",
    "GAME_DATE",
    "MATCHUP",
    "WL",
    "PTS",
    "REB",
    "AST",
    "FG_PCT",
    "FG3_PCT",
    "TOV",
    "PLUS_MINUS",
    "FGA",
    "FTA",
    "OREB",
]


def _safe_pct(series: pd.Series) -> pd.Series:
    s = series.copy()
    if s.dropna().empty:
        return s
    if s.dropna().max() <= 1.5:
        return s * 100
    return s


def fetch_team_games_for_season(season: str, pause_seconds: float = 0.7) -> pd.DataFrame:
    finder = leaguegamefinder.LeagueGameFinder(
        season_nullable=season,
        season_type_nullable="Regular Season",
        player_or_team_abbreviation="T",
        league_id_nullable="00",
    )
    df = finder.get_data_frames()[0].copy()
    df["SEASON"] = season
    time.sleep(pause_seconds)
    return df


def fetch_team_games_multi_season(seasons: list[str] | None = None) -> pd.DataFrame:
    seasons = seasons or SEASONS
    frames = []
    for season in seasons:
        print(f"Fetching season {season}...")
        frames.append(fetch_team_games_for_season(season))
    raw = pd.concat(frames, ignore_index=True)
    raw = raw.drop_duplicates(subset=["GAME_ID", "TEAM_ID"], keep="first")
    return raw


def build_team_game_dataset(raw_games: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in CORE_TEAM_COLS if c not in raw_games.columns]
    if missing:
        raise ValueError(f"Missing expected columns from leaguegamefinder: {missing}")

    df = raw_games[CORE_TEAM_COLS + ["SEASON"]].copy()
    df["WIN"] = (df["WL"] == "W").astype(int)

    # Opponent merge by GAME_ID (one row per team-game with matched opponent row)
    opp_cols = ["TEAM_ID", "TEAM_NAME", "PTS", "REB", "AST", "FG_PCT", "TOV", "FGA", "FTA", "OREB"]
    opp = df[["GAME_ID"] + opp_cols].copy()
    rename_map = {
        "TEAM_ID": "OPP_TEAM_ID",
        "TEAM_NAME": "OPP_TEAM_NAME",
        "PTS": "OPP_PTS",
        "REB": "OPP_REB",
        "AST": "OPP_AST",
        "FG_PCT": "OPP_FG_PCT",
        "TOV": "OPP_TOV",
        "FGA": "OPP_FGA",
        "FTA": "OPP_FTA",
        "OREB": "OPP_OREB",
    }
    opp = opp.rename(columns=rename_map)

    merged = df.merge(opp, on="GAME_ID", how="inner")
    merged = merged[merged["TEAM_ID"] != merged["OPP_TEAM_ID"]].copy()

    # One row per team-game
    merged = merged.drop_duplicates(subset=["GAME_ID", "TEAM_ID"], keep="first")

    # Differentials
    merged["PTS_DIFF"] = merged["PTS"] - merged["OPP_PTS"]
    merged["REB_DIFF"] = merged["REB"] - merged["OPP_REB"]
    merged["AST_DIFF"] = merged["AST"] - merged["OPP_AST"]
    merged["TOV_DIFF"] = merged["TOV"] - merged["OPP_TOV"]
    merged["FG_DIFF"] = merged["FG_PCT"] - merged["OPP_FG_PCT"]

    # Estimated possessions / pace-like game tempo feature
    team_poss = merged["FGA"] + 0.44 * merged["FTA"] - merged["OREB"] + merged["TOV"]
    opp_poss = merged["OPP_FGA"] + 0.44 * merged["OPP_FTA"] - merged["OPP_OREB"] + merged["OPP_TOV"]
    merged["PACE_EST"] = (team_poss + opp_poss) / 2

    merged["FG_PCT_PCT"] = _safe_pct(merged["FG_PCT"])
    merged["FG3_PCT_PCT"] = _safe_pct(merged["FG3_PCT"])
    merged["OPP_FG_PCT_PCT"] = _safe_pct(merged["OPP_FG_PCT"])
    merged["FG_DIFF_PCT_PTS"] = merged["FG_PCT_PCT"] - merged["OPP_FG_PCT_PCT"]

    return merged


def _threshold_table(df: pd.DataFrame, stat_col: str, thresholds: list[float], mode: str = ">=") -> pd.DataFrame:
    rows = []
    for t in thresholds:
        if mode == ">=":
            subset = df[df[stat_col] >= t]
        else:
            subset = df[df[stat_col] <= t]
        n = len(subset)
        p = subset["WIN"].mean() if n > 0 else np.nan
        rows.append({"threshold": t, "games": n, "win_probability": p})
    return pd.DataFrame(rows)


def _plot_threshold_curve(tbl: pd.DataFrame, title: str, x_label: str, output_path: Path) -> None:
    plt.figure(figsize=(8, 5))
    sns.lineplot(data=tbl, x="threshold", y="win_probability", marker="o")
    plt.ylim(0, 1)
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel("P(Win | condition)")
    plt.tight_layout()
    plt.savefig(output_path, dpi=220)
    plt.close()


def _combo_heatmap(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    x_thresholds: list[float],
    y_thresholds: list[float],
    x_mode: str,
    y_mode: str,
    title: str,
    output_path: Path,
    min_games: int = 150,
) -> pd.DataFrame:
    table = pd.DataFrame(index=y_thresholds, columns=x_thresholds, dtype=float)

    for y in y_thresholds:
        for x in x_thresholds:
            if x_mode == ">=":
                c1 = df[x_col] >= x
            else:
                c1 = df[x_col] <= x

            if y_mode == ">=":
                c2 = df[y_col] >= y
            else:
                c2 = df[y_col] <= y

            subset = df[c1 & c2]
            if len(subset) >= min_games:
                table.loc[y, x] = subset["WIN"].mean()
            else:
                table.loc[y, x] = np.nan

    plt.figure(figsize=(11, 7))
    sns.heatmap(table, cmap="YlGnBu", annot=True, fmt=".2f")
    plt.title(title)
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.tight_layout()
    plt.savefig(output_path, dpi=220)
    plt.close()
    return table


def run_eda_workflow(df: pd.DataFrame, plots_dir: Path | str = "plots", outputs_dir: Path | str = "outputs") -> dict:
    plots_dir = Path(plots_dir)
    outputs_dir = Path(outputs_dir)
    plots_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # 1) Correlation matrix
    corr_cols = [
        "PTS",
        "REB",
        "AST",
        "FG_PCT_PCT",
        "FG3_PCT_PCT",
        "TOV",
        "PTS_DIFF",
        "REB_DIFF",
        "AST_DIFF",
        "TOV_DIFF",
        "FG_DIFF_PCT_PTS",
        "WIN",
    ]
    corr_df = df[corr_cols].corr(numeric_only=True)
    corr_df.to_csv(outputs_dir / "correlation_matrix.csv")

    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_df, annot=True, cmap="coolwarm", center=0, fmt=".2f")
    plt.title("Correlation Matrix: Team Stats vs WIN")
    plt.tight_layout()
    plt.savefig(plots_dir / "correlation_heatmap.png", dpi=220)
    plt.close()

    # 2) Threshold probability curves
    thresholds = {
        "PTS": (list(range(90, 126, 5)), ">="),
        "REB": (list(range(35, 61, 2)), ">="),
        "AST": (list(range(15, 36, 2)), ">="),
        "FG_PCT_PCT": (list(range(40, 61, 2)), ">="),
        "FG3_PCT_PCT": (list(range(30, 51, 2)), ">="),
        "TOV": (list(range(8, 23, 1)), "<="),
        "OPP_TOV": (list(range(8, 23, 1)), ">="),
    }
    threshold_tables = {}
    for stat, (ts, mode) in thresholds.items():
        tbl = _threshold_table(df, stat, ts, mode=mode)
        threshold_tables[stat] = tbl
        tbl.to_csv(outputs_dir / f"threshold_table_{stat}.csv", index=False)
        label = f"{stat} threshold"
        mode_text = ">=" if mode == ">=" else "<="
        _plot_threshold_curve(
            tbl,
            title=f"P(Win | {stat} {mode_text} threshold)",
            x_label=label,
            output_path=plots_dir / f"threshold_curve_{stat}.png",
        )

    # 3) Multi-stat combination heatmaps
    combo1 = _combo_heatmap(
        df=df,
        x_col="REB",
        y_col="PTS",
        x_thresholds=list(range(36, 59, 2)),
        y_thresholds=list(range(95, 126, 5)),
        x_mode=">=",
        y_mode=">=",
        title="P(Win | PTS >= y AND REB >= x)",
        output_path=plots_dir / "combo_heatmap_pts_reb.png",
    )
    combo2 = _combo_heatmap(
        df=df,
        x_col="AST",
        y_col="FG_PCT_PCT",
        x_thresholds=list(range(18, 35, 2)),
        y_thresholds=list(range(42, 61, 2)),
        x_mode=">=",
        y_mode=">=",
        title="P(Win | FG% >= y AND AST >= x)",
        output_path=plots_dir / "combo_heatmap_fg_ast.png",
    )
    combo3 = _combo_heatmap(
        df=df,
        x_col="REB",
        y_col="TOV",
        x_thresholds=list(range(36, 59, 2)),
        y_thresholds=list(range(10, 19, 1)),
        x_mode=">=",
        y_mode="<=",
        title="P(Win | TOV <= y AND REB >= x)",
        output_path=plots_dir / "combo_heatmap_tov_reb.png",
    )
    combo1.to_csv(outputs_dir / "combo_pts_reb.csv")
    combo2.to_csv(outputs_dir / "combo_fg_ast.csv")
    combo3.to_csv(outputs_dir / "combo_tov_reb.csv")

    # 4) Logistic regression feature signal
    model_features = ["PTS", "REB", "AST", "FG_PCT_PCT", "FG3_PCT_PCT", "TOV"]
    model_df = df[model_features + ["WIN"]].dropna().copy()
    X = model_df[model_features].values
    y = model_df["WIN"].values

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    clf = LogisticRegression(max_iter=2000, random_state=42)
    clf.fit(Xs, y)
    coefs = pd.DataFrame({"feature": model_features, "coefficient": clf.coef_[0]})
    coefs["abs_coefficient"] = coefs["coefficient"].abs()
    coefs = coefs.sort_values("abs_coefficient", ascending=False)
    coefs.to_csv(outputs_dir / "logistic_coefficients.csv", index=False)

    plt.figure(figsize=(9, 5))
    sns.barplot(data=coefs, x="coefficient", y="feature", hue="feature", palette="vlag", legend=False)
    plt.axvline(0, color="black", linewidth=1)
    plt.title("Logistic Regression Coefficients (Standardized)")
    plt.tight_layout()
    plt.savefig(plots_dir / "logistic_coefficients.png", dpi=220)
    plt.close()

    # 5) Nonlinear effects: rolling win probability
    rolling_specs = [
        ("PTS", "rolling_win_prob_pts.png"),
        ("REB", "rolling_win_prob_reb.png"),
        ("AST", "rolling_win_prob_ast.png"),
        ("FG_PCT_PCT", "rolling_win_prob_fg_pct.png"),
        ("FG3_PCT_PCT", "rolling_win_prob_fg3_pct.png"),
        ("TOV", "rolling_win_prob_tov.png"),
    ]
    window = 1200
    for stat, file_name in rolling_specs:
        tmp = df[[stat, "WIN"]].dropna().sort_values(stat).reset_index(drop=True)
        tmp["rolling_win_prob"] = tmp["WIN"].rolling(window=window, min_periods=max(100, window // 5)).mean()
        plt.figure(figsize=(8, 5))
        sns.lineplot(data=tmp, x=stat, y="rolling_win_prob")
        plt.ylim(0, 1)
        plt.title(f"Rolling Win Probability vs {stat}")
        plt.tight_layout()
        plt.savefig(plots_dir / file_name, dpi=220)
        plt.close()

    # 6) Team style analysis and clustering
    style = (
        df.groupby(["SEASON", "TEAM_NAME"], as_index=False)
        .agg(
            PTS=("PTS", "mean"),
            REB=("REB", "mean"),
            AST=("AST", "mean"),
            FG_PCT=("FG_PCT_PCT", "mean"),
            FG3_PCT=("FG3_PCT_PCT", "mean"),
            PACE=("PACE_EST", "mean"),
        )
        .dropna()
    )
    style_features = ["PTS", "REB", "AST", "FG_PCT", "FG3_PCT", "PACE"]
    X_style = style[style_features].values
    X_style_scaled = StandardScaler().fit_transform(X_style)

    kmeans = KMeans(n_clusters=4, random_state=42, n_init=20)
    style["cluster"] = kmeans.fit_predict(X_style_scaled)

    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(X_style_scaled)
    style["pca1"] = coords[:, 0]
    style["pca2"] = coords[:, 1]
    style.to_csv(outputs_dir / "team_style_clusters.csv", index=False)
    style.groupby("cluster")[style_features].mean().to_csv(outputs_dir / "team_style_cluster_summary.csv")

    plt.figure(figsize=(10, 7))
    sns.scatterplot(
        data=style,
        x="pca1",
        y="pca2",
        hue="cluster",
        alpha=0.8,
        palette="tab10",
    )
    plt.title("Team Style Archetypes (KMeans) - PCA")
    plt.tight_layout()
    plt.savefig(plots_dir / "team_style_clusters_pca.png", dpi=220)
    plt.close()

    # 7) Distribution plots
    dist_cols = ["PTS", "REB", "AST", "FG_PCT_PCT", "FG3_PCT_PCT", "TOV"]
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    for ax, col in zip(axes.flatten(), dist_cols):
        sns.histplot(df[col].dropna(), kde=True, bins=35, ax=ax)
        ax.set_title(f"Distribution: {col}")
    plt.tight_layout()
    plt.savefig(plots_dir / "stat_distributions.png", dpi=220)
    plt.close()

    return {
        "correlation_matrix": corr_df,
        "threshold_tables": threshold_tables,
        "logistic_coefficients": coefs,
    }


def main() -> None:
    base_dir = Path(".")
    plots_dir = base_dir / "plots"
    outputs_dir = base_dir / "outputs"

    raw = fetch_team_games_multi_season(SEASONS)
    dataset = build_team_game_dataset(raw)

    dataset.to_csv(base_dir / "team_game_dataset.csv", index=False)
    run_eda_workflow(dataset, plots_dir=plots_dir, outputs_dir=outputs_dir)

    print("Pipeline completed.")
    print(f"Saved dataset: {base_dir / 'team_game_dataset.csv'}")
    print(f"Saved plots to: {plots_dir}")
    print(f"Saved analysis tables to: {outputs_dir}")


if __name__ == "__main__":
    main()
