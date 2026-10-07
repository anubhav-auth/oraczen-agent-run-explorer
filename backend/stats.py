from __future__ import annotations
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
def _pct_nearest_rank(sorted_vals: list, p: float):
    if not sorted_vals:
        return None
    idx = math.ceil(p / 100 * len(sorted_vals)) - 1
    return sorted_vals[max(0, min(idx, len(sorted_vals) - 1))]
def compute_stats(runs, meta: dict) -> dict:
    total = len(runs)
    by_status = dict(Counter(r.status for r in runs))
    by_agent = dict(Counter(r.agent for r in runs))
    eligible = [r for r in runs if r.status != "running"]
    succ = sum(1 for r in eligible if r.status == "succeeded")
    success_rate = succ / len(eligible) if eligible else 0.0
    from collections import defaultdict as dd
    per_agent: dict = dd(list)
    for r in runs:
        per_agent[r.agent].append(r)
    success_by_agent = {}
    for ag, sub in per_agent.items():
        elig = [r for r in sub if r.status != "running"]
        success_by_agent[ag] = sum(1 for r in elig if r.status == "succeeded") / len(elig) if elig else None
    durs = sorted(r.duration_ms for r in runs if isinstance(r.duration_ms, (int, float)) and r.duration_ms >= 0)
    median = statistics.median(durs) if durs else None
    p95 = _pct_nearest_rank(durs, 95)
    cost_by_agent: dict = defaultdict(float)
    unpriced_by_agent: dict = defaultdict(int)
    unpriced = 0
    for r in runs:
        if r.cost_usd is None:
            unpriced += 1
            unpriced_by_agent[r.agent] += 1
        else:
            cost_by_agent[r.agent] += r.cost_usd
    for ag in per_agent:
        cost_by_agent.setdefault(ag, 0.0)
        unpriced_by_agent.setdefault(ag, 0)
    per_day = Counter(r.started_at[:10] for r in runs)
    dates = sorted(r.started_at[:10] for r in runs)
    start = datetime.fromisoformat(dates[0].replace("Z", "+00:00")).date()
    end = datetime.fromisoformat(dates[-1].replace("Z", "+00:00")).date()
    runs_per_day = []
    d = start
    while d <= end:
        iso = d.isoformat()
        runs_per_day.append({"date": iso, "count": per_day.get(iso, 0)})
        d += timedelta(days=1)
    return {"total": total, "by_status": by_status, "by_agent": by_agent, "success_rate": success_rate, "success_by_agent": success_by_agent, "median_duration_ms": float(median) if median is not None else None, "p95_duration_ms": p95, "total_cost": sum(cost_by_agent.values()), "cost_by_agent": dict(cost_by_agent), "unpriced_count": unpriced, "unpriced_by_agent": dict(unpriced_by_agent), "runs_per_day": runs_per_day, "meta": meta}
