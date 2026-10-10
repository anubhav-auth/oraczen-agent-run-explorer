from __future__ import annotations
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta


def compute_stats_streaming(path: str, offsets: dict, duplicate_ids: list,
                             skipped_lines: int) -> dict:
    """Single streaming pass over the file; retains only counters, not rows.

    Same rules as compute_stats: running excluded from success rate and
    duration percentiles, negative durations excluded (but listed in meta),
    null costs counted in unpriced_*. Duplicate ids resolve keep-last via
    the offsets table (stale occurrences skipped).
    """
    from backend.loader import iter_live_raw  # deferred: avoids import cycle

    total = 0
    by_status: Counter = Counter()
    by_agent: Counter = Counter()
    eligible = 0
    succ = 0
    elig_by_agent: dict = defaultdict(int)
    succ_by_agent: dict = defaultdict(int)
    agents_seen: set = set()
    durs: list = []
    excluded_negative: list = []
    cost_by_agent: dict = defaultdict(float)
    unpriced_by_agent: dict = defaultdict(int)
    unpriced = 0
    per_day: Counter = Counter()
    min_day: str | None = None
    max_day: str | None = None

    for _off, raw in iter_live_raw(path, offsets):
        total += 1
        status = raw.get("status", "")
        agent = raw.get("agent", "")
        agents_seen.add(agent)
        by_status[status] += 1
        by_agent[agent] += 1
        if status != "running":
            eligible += 1
            elig_by_agent[agent] += 1
            if status == "succeeded":
                succ += 1
                succ_by_agent[agent] += 1
        dur = raw.get("duration_ms")
        if isinstance(dur, bool):
            pass
        elif isinstance(dur, (int, float)):
            if dur < 0:
                excluded_negative.append(raw.get("id", ""))
            else:
                durs.append(dur)
        cost = raw.get("cost_usd")
        if cost is None:
            unpriced += 1
            unpriced_by_agent[agent] += 1
        elif isinstance(cost, (int, float)) and not isinstance(cost, bool):
            cost_by_agent[agent] += cost
        day = str(raw.get("started_at", ""))[:10]
        if len(day) == 10:
            per_day[day] += 1
            if min_day is None or day < min_day:
                min_day = day
            if max_day is None or day > max_day:
                max_day = day

    success_rate = succ / eligible if eligible else 0.0
    success_by_agent = {
        ag: (succ_by_agent[ag] / elig_by_agent[ag] if elig_by_agent[ag] else None)
        for ag in agents_seen
    }
    durs.sort()
    median = statistics.median(durs) if durs else None
    p95 = _pct_nearest_rank(durs, 95)
    for ag in agents_seen:
        cost_by_agent.setdefault(ag, 0.0)
        unpriced_by_agent.setdefault(ag, 0)
    runs_per_day = []
    if min_day and max_day:
        d = datetime.fromisoformat(min_day).date()
        end = datetime.fromisoformat(max_day).date()
        while d <= end:
            iso = d.isoformat()
            runs_per_day.append({"date": iso, "count": per_day.get(iso, 0)})
            d += timedelta(days=1)
    meta = {"duplicate_ids": sorted(duplicate_ids), "skipped_lines": skipped_lines,
            "excluded_negative": sorted(excluded_negative)}
    return {"total": total, "by_status": dict(by_status), "by_agent": dict(by_agent),
            "success_rate": success_rate, "success_by_agent": success_by_agent,
            "median_duration_ms": float(median) if median is not None else None,
            "p95_duration_ms": p95, "total_cost": sum(cost_by_agent.values()),
            "cost_by_agent": dict(cost_by_agent), "unpriced_count": unpriced,
            "unpriced_by_agent": dict(unpriced_by_agent),
            "runs_per_day": runs_per_day, "meta": meta}
def _pct_nearest_rank(sorted_vals: list, p: float):
    if not sorted_vals:
        return None
    idx = math.ceil(p / 100 * len(sorted_vals)) - 1
    return sorted_vals[max(0, min(idx, len(sorted_vals) - 1))]
def compute_stats(runs, meta: dict) -> dict:
    if not runs:
        return {"total": 0, "by_status": {}, "by_agent": {}, "success_rate": 0.0, "success_by_agent": {}, "median_duration_ms": None, "p95_duration_ms": None, "total_cost": 0.0, "cost_by_agent": {}, "unpriced_count": 0, "unpriced_by_agent": {}, "runs_per_day": [], "meta": meta}
    total = len(runs)
    by_status = dict(Counter(r.status for r in runs))
    by_agent = dict(Counter(r.agent for r in runs))
    eligible = [r for r in runs if r.status != "running"]
    succ = sum(1 for r in eligible if r.status == "succeeded")
    success_rate = succ / len(eligible) if eligible else 0.0
    per_agent: dict = defaultdict(list)
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
