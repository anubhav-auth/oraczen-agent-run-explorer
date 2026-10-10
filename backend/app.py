from __future__ import annotations
import os
from datetime import datetime, timezone
from itertools import islice
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from backend.loader import build_offset_index, iter_live_raw, read_run_at, summarize_raw
from backend.models import RunsPage, RunSummary, RunDetail, Stats
from backend.stats import compute_stats_streaming
from backend.explain import MockExplainProvider
RUNS_PATH = os.environ.get("RUNS_PATH", "data/runs.jsonl")
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")
ALLOW_ORIGINS = [o.strip() for o in FRONTEND_ORIGIN.split(",") if o.strip()]
app = FastAPI(title="Agent Run Explorer")
app.add_middleware(CORSMiddleware, allow_origins=ALLOW_ORIGINS, allow_methods=["*"], allow_headers=["*"])
# Streaming startup: two sequential passes over the file, flat memory.
# Only retained state: id -> byte offset (~20MB per 1M rows) + one stats dict.
_OFFSETS, _DUP_IDS, _SKIPPED = build_offset_index(RUNS_PATH)
_STATS_CACHE = compute_stats_streaming(RUNS_PATH, _OFFSETS, _DUP_IDS, _SKIPPED)

def _parse_dt(s: str | None, *, end_of_day: bool = False) -> datetime | None:
    if not s:
        return None
    s = s.strip()
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        # Naive input (e.g. date-only "2026-08-01" from <input type="date">):
        # assume UTC so it never meets an aware timestamp unarmed.
        if end_of_day and len(s) == 10:  # pure YYYY-MM-DD upper bound
            dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

def _iter_filtered(status, agent, started_from, started_to, q, tools=None):
    """Stream matching summaries: one line in, keep/skip, throw away.

    Filters apply cheapest-first (status/agent before date/prompt/steps)
    so most lines are discarded without parsing dates or touching steps.
    Yields small summary dicts (no steps objects ever built).
    """
    try:
        sf = _parse_dt(started_from)
        st = _parse_dt(started_to, end_of_day=True)
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid date format, expected ISO 8601")
    qn = q.strip().lower() if q else None
    for _off, raw in iter_live_raw(RUNS_PATH, _OFFSETS):
        if status and raw.get("status") not in status:
            continue
        if agent and raw.get("agent") not in agent:
            continue
        if sf or st:
            try:
                rd = _parse_dt(raw.get("started_at", ""))
            except ValueError:
                continue
            if sf and (rd is None or rd < sf):
                continue
            if st and (rd is None or rd > st):
                continue
        if qn and qn not in str(raw.get("prompt") or "").strip().lower():
            continue
        if tools:
            steps = raw.get("steps") or []
            if not any(isinstance(s, dict) and s.get("tool") in tools for s in steps):
                continue
        yield summarize_raw(raw)

def _sort_dicts(rows, sort, order):
    reverse = order == "desc"
    if sort == "started_at":
        return sorted(rows, key=lambda r: r.get("started_at") or "", reverse=reverse)
    nulls = [r for r in rows if r.get(sort) is None]
    vals = [r for r in rows if r.get(sort) is not None]
    vals = sorted(vals, key=lambda r: r[sort], reverse=reverse)
    return vals + nulls

@app.get("/api/runs", response_model=RunsPage)
def list_runs(page: int = Query(default=1, ge=1), page_size: int = Query(default=25, ge=1, le=100), status: list[str] | None = Query(default=None), agent: list[str] | None = Query(default=None), started_from: str | None = None, started_to: str | None = None, q: str | None = None, tool: list[str] | None = Query(default=None), sort: str = Query(default="started_at", pattern="^(started_at|duration_ms|cost_usd)$"), order: str = Query(default="desc", pattern="^(asc|desc)$")):
    # NOTE (no-DB tradeoff): total + sort need the full match set, so matches
    # are materialized — but each is a small summary dict (steps never built
    # into objects). Memory is O(matches x summary), not O(N x full runs).
    # Next step at larger scale: pre-sorted files or keyset cursor pagination.
    matched = list(_iter_filtered(status, agent, started_from, started_to, q, tool))
    ordered = _sort_dicts(matched, sort, order)
    total = len(ordered)
    start = (page - 1) * page_size
    items = [RunSummary.model_validate(r) for r in islice(ordered, start, start + page_size)]
    return RunsPage(items=items, total=total, page=page, page_size=page_size)


@app.get("/api/runs/{run_id}", response_model=RunDetail)
def get_run(run_id: str):
    off = _OFFSETS.get(run_id)
    if off is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    try:
        run = read_run_at(RUNS_PATH, off)
    except Exception:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    return RunDetail(**{**run.model_dump(), "steps": sorted(run.steps, key=lambda s: s.index)})


@app.get("/api/stats", response_model=Stats)
def get_stats():
    # Precomputed once at startup via one streaming pass; served, not recomputed.
    return _STATS_CACHE


@app.post("/api/runs/{run_id}/explain")
async def explain_run(run_id: str):
    off = _OFFSETS.get(run_id)
    if off is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    try:
        run = read_run_at(RUNS_PATH, off)
    except Exception:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    provider = MockExplainProvider()
    return StreamingResponse(provider.stream(run), media_type="text/plain")
