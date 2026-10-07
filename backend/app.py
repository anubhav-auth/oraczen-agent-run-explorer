from __future__ import annotations
import os
from datetime import datetime
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from backend.loader import load_runs
from backend.models import RunsPage, RunSummary
RUNS_PATH = os.environ.get("RUNS_PATH", "data/runs.jsonl")
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")
app = FastAPI(title="Agent Run Explorer")
app.add_middleware(CORSMiddleware, allow_origins=[FRONTEND_ORIGIN], allow_methods=["*"], allow_headers=["*"])
_RUNS, _META = load_runs(RUNS_PATH)
_BY_ID = {r.id: r for r in _RUNS}
def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))
def _filter(status, agent, started_from, started_to, q):
    sf = _parse_dt(started_from)
    st = _parse_dt(started_to)
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
def list_runs(page: int = Query(default=1, ge=1), page_size: int = Query(default=25, ge=1, le=100), status: list[str] | None = Query(default=None), agent: list[str] | None = Query(default=None), started_from: str | None = None, started_to: str | None = None, q: str | None = None, sort: str = Query(default="started_at", pattern="^(started_at|duration_ms|cost_usd)$"), order: str = Query(default="desc", pattern="^(asc|desc)$")):
    filtered = _filter(status, agent, started_from, started_to, q)
    ordered = _sort(filtered, sort, order)
    total = len(ordered)
    start = (page - 1) * page_size
    items = [RunSummary.model_validate(r.model_dump(exclude={"steps"})) for r in ordered[start:start + page_size]]
    return RunsPage(items=items, total=total, page=page, page_size=page_size)
