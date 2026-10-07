# Agent Run Explorer

Browse and understand agent runs: filterable run list, per-run step traces with streaming explanations, and a stats dashboard. Backend FastAPI + frontend Next.js, talking over HTTP.

## Prereqs

Python 3.11+ and Node 20+. Nothing else.

## Run it

Terminal 1 — backend (port 8000):

```bash
pip install -r backend/requirements.txt
RUNS_PATH=data/runs.jsonl python -m uvicorn backend.app:app --port 8000
```

Terminal 2 — frontend (port 3000):

```bash
npm install --prefix frontend
npm run dev --prefix frontend
```

Open http://localhost:3000/runs. Dashboard at http://localhost:3000/dashboard.

## Env

See `.env.example`. Backend: `RUNS_PATH`, `EXPLAIN_PROVIDER` (mock), `EXPLAIN_DELAY_MS`, `PORT`, `FRONTEND_ORIGIN`. Frontend: `API_URL` (server fetch), `NEXT_PUBLIC_API_URL` (browser explain POST). Defaults work locally with no keys.

## Tests

```bash
pytest backend/tests -v
npm test --prefix frontend -- --run
```

## Decisions

See `DECISIONS.md` (null costs, running runs, duplicate `run_0031`, global stats, frontend test note).

## Notes

- Dataset: 201 lines in `data/runs.jsonl`, 200 unique runs after dedupe. Deliberately messy; loader warns on stderr and never silently drops records.
- Design specs and plans: `docs/superpowers/specs/`, `docs/superpowers/plans/`.

## Docker

Prereq: docker.
Boot: `docker compose up --build`.
UI http://localhost:3000/runs, API http://localhost:8000/api/stats.
Stop: `docker compose down`.
