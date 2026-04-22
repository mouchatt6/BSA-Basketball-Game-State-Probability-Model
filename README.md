# NBA Win Probability Portable Bundle

This folder is a clean, portable package with only what is needed to run:

- `pipeline/` - Python data pipeline (NBA API pull + EDA outputs)
- `frontend/` - React + TypeScript interactive win probability prototype

No notebooks, no old experiments, no extra artifacts.

## Folder Layout

- `pipeline/data_pipeline.py`
- `pipeline/requirements.txt`
- `frontend/` (Vite React app)

## 1) Run the Data Pipeline

From this folder:

```bash
cd pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python data_pipeline.py
```

Outputs are created in `pipeline/`:

- `team_game_dataset.csv`
- `plots/`
- `outputs/`

## 2) Run the Frontend Prototype

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Then open the local URL printed by Vite (usually `http://localhost:5173`).

## Notes

- Frontend model config currently includes:
  - team baselines/stds from historical dataset
  - team baseline probability seeded from 2025 spread-derived odds baseline
- The calculator logic is intentionally simple and interpretable.
- Future models can replace the math in `src/utils/winProbability.ts`.
