# Decisions
1. Null cost: excluded from sums, `unpriced_count` overall + per agent, UI must show "excludes 3 unpriced".
2. Running: excluded from success-rate denominator and duration percentiles; sorted nulls-last. Success = succeeded / (total - running) = 139/191.
3. Duplicate run_0031: keep-last (running) + warn + `meta.duplicate_ids`; total is 200 unique, not 201 lines.
4. Stats always global; list filters do not affect /api/stats. Documented here and in plan.
Negative duration run_0064 stored as-is, excluded from median/p95, listed in `meta.excluded_negative`.
p95 = nearest-rank ceil(0.95*n)-1; median over >= 0 durations (n=190): 23593.0 / 41530.
20M rows: Postgres + (agent,status,started_at) indexes, server-side filter, pre-aggregated stats, cursor pagination.

## Frontend tests
Vitest covers query helpers and pagination labels; no component/e2e tests — no backend fixture harness in CI and the risky logic (filter composition, stats math) already lives in tested backend code. Next step with another day: Playwright smoke test /runs -> detail -> explain.

## Frontend notes
Unknown run URL renders the Next not-found UI but with HTTP 200: the layout streams before the backend fetch resolves, so notFound() fires after streaming starts (documented Next fallback, page still gets noindex). API-level 404s are real 404s.

## Skipped optionals (and why)
Built: tool filter, docker compose, step deep-link auto-expand, numbered pagination.
Skipped: list keyboard nav — mouse/touch + native focus already serve the flows, custom key handling risked hijacking screen-reader keys for little gain. Request duration/count indicator — backend answers in single-digit ms locally so the indicator would only prove what timing already shows; skipped as reviewer theater. Cursor pagination — offset is correct at 200 rows; cursors pay off past thousands. 500-step perf — max in dataset is 5 steps; virtualization would be speculative complexity.
