from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import ttk

import pandas as pd


@dataclass
class Matchup:
    date: str
    away: str
    home: str
    spread: float
    whos_favored: str
    score_away: int
    score_home: int

    @property
    def signed_spread_home(self) -> float:
        return self.spread if self.whos_favored == "home" else -self.spread

    @property
    def home_win(self) -> int:
        return int(self.score_home > self.score_away)


class MatchupSliderApp:
    def __init__(self, root: tk.Tk, project_root: Path) -> None:
        self.root = root
        self.root.title("Win Prob V1 - Matchup Slider")

        self.project_root = project_root
        self.model = self._load_json(project_root / "outputs" / "baseline_params.json")
        self.weights = self._load_json(project_root / "outputs" / "position_stat_weights.json")
        self.matchups = self._load_matchups(project_root.parent / "nba_2008-2025.csv")

        self.player_rows: list[dict[str, object]] = []
        self._build_ui()
        self._on_matchup_change()

    @staticmethod
    def _load_json(path: Path) -> dict:
        return json.loads(path.read_text())

    @staticmethod
    def _abbr_to_team_name(abbr: str) -> str:
        mapping = {
            "bos": "Boston Celtics",
            "mia": "Miami Heat",
        }
        return mapping.get(abbr.lower(), abbr.upper())

    def _load_matchups(self, csv_path: Path) -> list[Matchup]:
        df = pd.read_csv(csv_path)
        df = df[(df["season"] == 2025) & (df["regular"] == True)].copy()
        # Keep one rivalry for quick testing and add any reverse fixtures if present.
        df = df[((df["away"] == "bos") & (df["home"] == "mia")) | ((df["away"] == "mia") & (df["home"] == "bos"))]
        df = df.sort_values("date").reset_index(drop=True)
        rows: list[Matchup] = []
        for _, r in df.iterrows():
            rows.append(
                Matchup(
                    date=str(r["date"]),
                    away=str(r["away"]),
                    home=str(r["home"]),
                    spread=float(r["spread"]),
                    whos_favored=str(r["whos_favored"]).lower(),
                    score_away=int(r["score_away"]),
                    score_home=int(r["score_home"]),
                )
            )
        if not rows:
            raise RuntimeError("No 2025 BOS/MIA games found in nba_2008-2025.csv.")
        return rows

    @staticmethod
    def _logistic(x: float) -> float:
        return 1.0 / (1.0 + math.exp(-x))

    def _baseline_prob(self, signed_spread_home: float) -> float:
        intercept = float(self.model["intercept"])
        coef = float(self.model["spread_coef"])
        return self._logistic(intercept + coef * signed_spread_home)

    def _compute_delta_margin(self) -> float:
        base = self.weights["stat_coefficients"]
        mult = self.weights["position_multipliers"]
        total = 0.0
        for row in self.player_rows:
            side = row["side"]
            pos = row["position"]
            sign = 1.0 if side == "home" else -1.0
            pts = float(row["pts"].get())
            reb = float(row["reb"].get())
            ast = float(row["ast"].get())

            pts_w = float(base["points"]) * float(mult[pos]["points"])
            reb_w = float(base["rebounds"]) * float(mult[pos]["rebounds"])
            ast_w = float(base["assists"]) * float(mult[pos]["assists"])
            total += sign * (pts_w * pts + reb_w * reb + ast_w * ast)
        return total

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Matchup (2025):").pack(side=tk.LEFT)
        self.matchup_var = tk.StringVar()
        options = [f"{m.date} | {m.away.upper()} @ {m.home.upper()}" for m in self.matchups]
        self.matchup_combo = ttk.Combobox(top, textvariable=self.matchup_var, values=options, state="readonly", width=40)
        self.matchup_combo.current(0)
        self.matchup_combo.pack(side=tk.LEFT, padx=8)
        self.matchup_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_matchup_change())

        self.info_var = tk.StringVar(value="")
        ttk.Label(self.root, textvariable=self.info_var, padding=(10, 4)).pack(anchor="w")

        self.result_var = tk.StringVar(value="")
        ttk.Label(self.root, textvariable=self.result_var, padding=(10, 2)).pack(anchor="w")

        canvas_wrap = ttk.Frame(self.root)
        canvas_wrap.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
        canvas = tk.Canvas(canvas_wrap, height=500)
        scrollbar = ttk.Scrollbar(canvas_wrap, orient=tk.VERTICAL, command=canvas.yview)
        self.slider_frame = ttk.Frame(canvas)
        self.slider_frame.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.slider_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._build_player_sliders()

        btn_row = ttk.Frame(self.root, padding=10)
        btn_row.pack(fill=tk.X)
        ttk.Button(btn_row, text="Reset Sliders", command=self._reset_sliders).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Recompute", command=self._recompute).pack(side=tk.LEFT, padx=8)

        self._recompute()

    def _build_player_sliders(self) -> None:
        self.player_rows.clear()
        for widget in self.slider_frame.winfo_children():
            widget.destroy()

        # Simple 5-man layout per team for testing.
        home_positions = ["G", "G", "F", "F", "C"]
        away_positions = ["G", "G", "F", "F", "C"]

        ttk.Label(self.slider_frame, text="Home Player Deltas (vs baseline):", padding=(0, 6)).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(self.slider_frame, text="Away Player Deltas (vs baseline):", padding=(20, 6)).grid(
            row=0, column=4, sticky="w"
        )

        for i in range(5):
            self._add_player_row(row=1 + i, col_start=0, team_side="home", label=f"Home {home_positions[i]}{i+1}", pos=home_positions[i])
            self._add_player_row(row=1 + i, col_start=4, team_side="away", label=f"Away {away_positions[i]}{i+1}", pos=away_positions[i])

    def _add_player_row(self, row: int, col_start: int, team_side: str, label: str, pos: str) -> None:
        ttk.Label(self.slider_frame, text=f"{label} ({pos})").grid(row=row, column=col_start, sticky="w", padx=(0, 6))
        pts = tk.DoubleVar(value=0.0)
        reb = tk.DoubleVar(value=0.0)
        ast = tk.DoubleVar(value=0.0)

        self._add_scale(self.slider_frame, row, col_start + 1, pts, "PTS")
        self._add_scale(self.slider_frame, row, col_start + 2, reb, "REB")
        self._add_scale(self.slider_frame, row, col_start + 3, ast, "AST")

        self.player_rows.append(
            {"side": team_side, "position": pos, "pts": pts, "reb": reb, "ast": ast}
        )

    def _add_scale(self, parent: ttk.Frame, row: int, col: int, var: tk.DoubleVar, short: str) -> None:
        wrap = ttk.Frame(parent)
        wrap.grid(row=row, column=col, padx=2, pady=2, sticky="w")
        ttk.Label(wrap, text=short).pack(side=tk.LEFT)
        scale = tk.Scale(
            wrap,
            variable=var,
            from_=-10,
            to=10,
            orient=tk.HORIZONTAL,
            resolution=1,
            length=120,
            command=lambda _v: self._recompute(),
        )
        scale.pack(side=tk.LEFT)

    def _current_matchup(self) -> Matchup:
        idx = self.matchup_combo.current()
        return self.matchups[max(0, idx)]

    def _on_matchup_change(self) -> None:
        m = self._current_matchup()
        self.info_var.set(
            (
                f"{self._abbr_to_team_name(m.away)} @ {self._abbr_to_team_name(m.home)} | "
                f"Spread={m.spread:.1f} ({m.whos_favored}) | Final: {m.score_away}-{m.score_home}"
            )
        )
        self._reset_sliders()
        self._recompute()

    def _reset_sliders(self) -> None:
        for row in self.player_rows:
            row["pts"].set(0.0)
            row["reb"].set(0.0)
            row["ast"].set(0.0)
        self._recompute()

    def _recompute(self) -> None:
        m = self._current_matchup()
        base_spread = m.signed_spread_home
        delta_margin = self._compute_delta_margin()
        effective_spread = base_spread + delta_margin

        baseline_prob = self._baseline_prob(base_spread)
        adjusted_prob = self._baseline_prob(effective_spread)

        actual_txt = "HOME WIN" if m.home_win == 1 else "AWAY WIN"
        pred_base = "HOME" if baseline_prob >= 0.5 else "AWAY"
        pred_adj = "HOME" if adjusted_prob >= 0.5 else "AWAY"

        self.result_var.set(
            (
                f"Baseline P(home): {baseline_prob:.3f} | Adjusted P(home): {adjusted_prob:.3f} | "
                f"Delta margin: {delta_margin:+.2f} | Pred(base/adj): {pred_base}/{pred_adj} | "
                f"Actual: {actual_txt}"
            )
        )


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    root = tk.Tk()
    app = MatchupSliderApp(root=root, project_root=project_root)
    _ = app
    root.mainloop()


if __name__ == "__main__":
    main()
