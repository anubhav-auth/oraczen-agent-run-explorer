# Backend Design — Agent Run Explorer

Date: 2026-10-07. Scope: FastAPI backend + API contract for Next.js. No frontend code yet.

## Data grounding

- Source `data/runs.jsonl`: 201 lines, 200 unique IDs after dedupe.
- Duplicate breaker: `run_0031` line 75 (`succeeded`) vs line 187 (`running`). Same `started_at`/`prompt`. Decision: keep-last + warn.
- `run_0064` `duration_ms=-4000` (`ended_at` before `started_at`). Stored as-is, excluded from duration stats, logged.
- Null `cost_usd` ×3: `run_0008` (cancelled), `run_0042` + `run_0153` (succeeded). Excluded from sums, exposed as `unpriced_count`.
- Empty `steps`: `run_0089` (failed with `SchemaMismatch step_index 3` — error points past end, interesting edge).
- `running` ×10 after dedupe (9 raw + dup): no `ended_at`/`duration_ms`. Excluded from success-rate denominator and duration percentiles. Sort nulls-last.
- Hand-verified globals (post-dedupe): total 200, success 139/191 = 0.7277 excl running; durations n=190, median 23593.0, p95 nearest-rank 41530; cost total ≈8.744 minus dup delta; days 2026-07-20→2026-08-31.
- Prompts: max 122 chars, emoji (🔥), newlines, French `run_0121`, padded `run_0172`. Search must be case-insensitive substring on trimmed text.

## Architecture

Minimal layered FastAPI, in-memory at startup. `loader.py` owns file → validated models; `app.py` owns HTTP/filter/sort/page; `stats.py` owns pure aggregation; `explain.py` owns provider interface + mock streaming. No DB, no pandas. CORS enabled for Next.js.

## Components

1. `backend/models.py` — Pydantic v2 `Step`, `RunSummary` (no steps), `RunDetail` (with steps), `RunsPage`, `Stats`. Dates pass through as ISO `Z` strings; filtering parses internally.
2. `backend/loader.py` — `load_runs(path) -> (runs, meta)`. Line-by-line json, skip+count parse failures, dict-overwrite dedupe collecting `duplicate_ids`, Pydantic validate, warn on negative duration / null cost (counts only, no mutation).
3. `backend/app.py` — creates app, loads once at startup, `GET /api/runs` (AND across types, OR within multi-values, `q` on prompt, nulls-last sort, offset page), `GET /api/runs/{id}` (404 JSON), `GET /api/stats` (always global), `POST /api/runs/{id}/explain` (StreamingResponse text/plain, 404 pre-stream).
4. `backend/stats.py` — `compute_stats(runs, meta)`: counts, success excl running overall+per-agent, median + p95 nearest-rank over `duration_ms >= 0`, cost sums excl null + unpriced counts, per-day zero-filled range, meta passthrough.
5. `backend/explain.py` — `ExplainProvider` protocol + `MockExplainProvider`: deterministic 3-part text (what run did / steps+tools+tokens / failure location or success line), async generator with `EXPLAIN_DELAY_MS` sleep per sentence.

## Data flow

Boot: `RUNS_PATH` → `load_runs` → `app.state.runs` + `dict`. Request: parse query → filter list → sort (nulls-last) → paginate → serialize without steps. Stats: single pass over in-memory list. Explain: lookup by id → 404 or stream mock chunks.

## Error handling

- Unknown id → 404 `{"detail": ...}` on detail + explain (before streaming starts).
- Bad query (bad date, bad sort) → 422 from FastAPI validation.
- Corrupt JSONL line → skipped + counted in `meta.skipped_lines`, boot continues.
- Negative duration / null cost / empty steps → preserved in API, excluded only where documented, surfaced in `meta`/counts so UI can be honest.

## Testing

- `test_runs`: two filters compose (agent+status), pagination total matches filtered count, `q` finds padded/French prompt, sort nulls-last.
- `test_stats`: hand values — total 200, success 139/191, median 23593.0, p95 41530, unpriced 3, dup `run_0031` resolves to running.
- `test_explain`: streams chunks (not one blob), deterministic, 404 on missing id.
