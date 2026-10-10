from __future__ import annotations
import os
from datetime import datetime, timezone
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from backend.loader import load_runs
from backend.models import RunsPage, RunSummary, RunDetail, Stats
from backend.stats import compute_stats
from backend.explain import MockExplainProvider
RUNS_PATH = os.environ.get("RUNS_PATH", "data/runs.jsonl")
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")
ALLOW_ORIGINS = [o.strip() for o in FRONTEND_ORIGIN.split(",") if o.strip()]
app = FastAPI(title="Agent Run Explorer")
app.add_middleware(CORSMiddleware, allow_origins=ALLOW_ORIGINS, allow_methods=["*"], allow_headers=["*"])
_RUNS, _META = load_runs(RUNS_PATH)
_BY_ID = {r.id: r for r in _RUNS}

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

def _filter(status, agent, started_from, started_to, q, tools=None):
    try:
        sf = _parse_dt(started_from)
        st = _parse_dt(started_to, end_of_day=True)
    except ValueError:
        raise HTTPException(status_code=422, detail="invalid date format, expected ISO 8601")
    qn = q.strip().lower() if q else None
    out = []
    for r in _RUNS:
        if status and r.status not in status:
            continue
        if agent and r.agent not in agent:
            continue
        rd = _parse_dt(r.started_at)
        if sf and (rd is None or rd < sf):
            continue
        if st and (rd is None or rd > st):
            continue
        if qn and qn not in (r.prompt or "").strip().lower():
            continue
        if tools and not any(s.tool in tools for s in r.steps):
            continue
        out.append(r)
    return out

def _sort(runs, sort, order):
    reverse = order == "desc"
    if sort == "started_at":
        return sorted(runs, key=lambda r: r.started_at, reverse=reverse)
    key = "duration_ms" if sort == "duration_ms" else "cost_usd"
    nulls = [r for r in runs if getattr(r, key) is None]
    vals = [r for r in runs if getattr(r, key) is not None]
    vals = sorted(vals, key=lambda r: getattr(r, key), reverse=reverse)
    return vals + nulls
    
@app.get("/api/runs", response_model=RunsPage)
def list_runs(page: int = Query(default=1, ge=1), page_size: int = Query(default=25, ge=1, le=100), status: list[str] | None = Query(default=None), agent: list[str] | None = Query(default=None), started_from: str | None = None, started_to: str | None = None, q: str | None = None, tool: list[str] | None = Query(default=None), sort: str = Query(default="started_at", pattern="^(started_at|duration_ms|cost_usd)$"), order: str = Query(default="desc", pattern="^(asc|desc)$")):
    filtered = _filter(status, agent, started_from, started_to, q, tool)
    ordered = _sort(filtered, sort, order)
    total = len(ordered)
    start = (page - 1) * page_size
    items = [RunSummary.model_validate(r.model_dump(exclude={"steps"})) for r in ordered[start:start + page_size]]
    return RunsPage(items=items, total=total, page=page, page_size=page_size)


@app.get("/api/runs/{run_id}", response_model=RunDetail)
def get_run(run_id: str):
    run = _BY_ID.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    return RunDetail(**{**run.model_dump(), "steps": sorted(run.steps, key=lambda s: s.index)})


@app.get("/api/stats", response_model=Stats)
def get_stats():
    return compute_stats(_RUNS, _META)


@app.post("/api/runs/{run_id}/explain")
async def explain_run(run_id: str):
    run = _BY_ID.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    provider = MockExplainProvider()
    return StreamingResponse(provider.stream(run), media_type="text/plain")
