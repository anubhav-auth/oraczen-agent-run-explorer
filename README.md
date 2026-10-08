# Agent Run Explorer

Browse and understand agent runs: filterable run list, per-run step traces with streaming explanations, and a stats dashboard. Backend FastAPI + frontend Next.js, talking over HTTP.

## What you get

- `/runs`: filter by status, agent, tool, date range; search prompts; sort; paginated with shareable URLs; table on desktop, cards on phones.
- `/runs/[id]`: metadata, error callout, expandable steps with tools, durations, tokens; streaming "Explain this run"; `#step-N` deep-links auto-expand.
- `/dashboard`: totals, success rates, median/p95 durations, per-agent costs (unpriced rows called out), runs-per-day — hand-drawn SVG charts, no client math.

## Brief coverage (decisions and skipped-item reasons in `DECISIONS.md`)

Must-build: all done — composed list filters, detail + 404, global stats, streaming mock explain, backend + frontend tests.
Should-build: tool filter and step deep-links done; keyboard nav and request-timing indicator skipped.
Stretch: Docker Compose done; cursor pagination and 500-step handling skipped (offset is right at 200 rows; max in data is 5 steps).

## Prereqs

Python 3.11+ and Node 20+. Nothing else.

## Run it

Fastest:

```bash
make install
make dev
```

`make dev` starts both services and prints the links. For fast page switches (dev compiles per route), use `make prod` instead. Other targets: `make test` (both suites), `make build`, `make stop`. Manual alternative:

Terminal 1 — backend (port 8000):

```bash
python -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
RUNS_PATH=data/runs.jsonl .venv/bin/python -m uvicorn backend.app:app --port 8000
```

Terminal 2 — frontend (port 3000):

```bash
npm install --prefix frontend
npm run dev --prefix frontend
```

Open http://localhost:3000/runs. Dashboard at http://localhost:3000/dashboard.

## Env

See `.env.example`. Backend: `RUNS_PATH`, `EXPLAIN_PROVIDER` (mock), `EXPLAIN_DELAY_MS`, `PORT`, `FRONTEND_ORIGIN`. Frontend: `API_URL` (read by the server at request time), `NEXT_PUBLIC_API_URL` (baked in at build time for the browser Explain button — rebuild after changing it). Defaults work locally with no keys.

## Tests

```bash
pytest backend/tests -v
npm test --prefix frontend -- --run
```

## Decisions

See `DECISIONS.md` (null costs, running runs, duplicate `run_0031`, global stats, frontend test note).

## Notes

- Dataset: 201 lines in `data/runs.jsonl`, 200 unique runs after dedupe. Deliberately messy; loader warns on stderr and never silently drops records.

## Docker

Prereq: docker.
Boot: `docker compose up --build`.
UI http://localhost:3000/runs, API http://localhost:8000/api/stats.
Stop: `docker compose down`.
