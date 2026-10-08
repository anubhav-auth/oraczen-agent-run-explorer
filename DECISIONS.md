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

## Why two API URLs
`API_URL` serves server components (Node-side); `NEXT_PUBLIC_API_URL` serves the Explain button in the browser, since Next only inlines `NEXT_PUBLIC_*` vars into client JS — a plain var would be `undefined` there and every Explain click would fail. Strictly, one var (the public one, readable server-side too) would cover both sides today since the URL isn't secret. Kept the split anyway: server-only config stays out of the browser bundle by construction, so a future internal URL or secret can't leak through a copy-paste. This exact bug bit us once: server code briefly read `NEXT_PUBLIC_API_URL` first, Next inlined the build-time value, and docker-compose served error pages while the runtime `API_URL` was ignored — caught by reading the compiled bundle.

## Why the UI is plain
The brief says visual polish is not scored but usability is, so every styling choice buys function: plain CSS with zero UI dependencies (nothing to install, nothing to break on a reviewer's machine), system font stack, no animations (nothing to distract, nothing to honor reduced-motion for), status pills as the only color — always paired with the status word itself, never color-alone. Server-rendered pages keep it fast on phones, which is where the responsive table-to-cards switch matters most.

## Skipped optionals (and why)
Built: tool filter, docker compose, step deep-link auto-expand, numbered pagination.
Skipped: list keyboard nav — mouse/touch + native focus already serve the flows, custom key handling risked hijacking screen-reader keys for little gain. Request duration/count indicator — backend answers in single-digit ms locally so the indicator would only prove what timing already shows; skipped as reviewer theater. Cursor pagination — offset is correct at 200 rows; cursors pay off past thousands. 500-step perf — max in dataset is 5 steps; virtualization would be speculative complexity.
