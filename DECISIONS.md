# Decisions
1. Null cost: excluded from sums, `unpriced_count` overall + per agent, UI must show "excludes 3 unpriced".
2. Running: excluded from success-rate denominator and duration percentiles; sorted nulls-last. Success = succeeded / (total - running) = 139/191.
3. Duplicate run_0031: keep-last (running) + warn + `meta.duplicate_ids`; total is 200 unique, not 201 lines.
4. Stats always global; list filters do not affect /api/stats. Documented here and in plan.
Negative duration run_0064 stored as-is, excluded from median/p95, listed in `meta.excluded_negative`.
p95 = nearest-rank ceil(0.95*n)-1; median over >= 0 durations (n=190): 23593.0 / 41530.
20M rows: Postgres + (agent,status,started_at) indexes, server-side filter, pre-aggregated stats, cursor pagination.
