from __future__ import annotations
import json
import sys
from backend.models import RunDetail
def load_runs(path: str) -> tuple[list[RunDetail], dict]:
    by_id: dict[str, RunDetail] = {}
    duplicate_ids: list[str] = []
    seen: set[str] = set()
    skipped_lines = 0
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as e:
                skipped_lines += 1
                print(f"warn: skip line {lineno}: {e}", file=sys.stderr)
                continue
            rid = raw.get("id")
            if rid in seen and rid not in duplicate_ids:
                duplicate_ids.append(rid)
                print(f"warn: duplicate id {rid}, keeping last", file=sys.stderr)
            seen.add(rid)
            try:
                run = RunDetail.model_validate(raw)
            except Exception as e:
                skipped_lines += 1
                print(f"warn: skip {rid} line {lineno}: {e}", file=sys.stderr)
                continue
            if isinstance(run.duration_ms, (int, float)) and run.duration_ms < 0:
                print(f"warn: negative duration {rid}={run.duration_ms}", file=sys.stderr)
            if run.cost_usd is None:
                print(f"warn: null cost {rid}", file=sys.stderr)
            by_id[rid] = run
    runs = list(by_id.values())
    meta = {"duplicate_ids": sorted(duplicate_ids), "skipped_lines": skipped_lines, "excluded_negative": sorted(r.id for r in runs if isinstance(r.duration_ms, (int, float)) and r.duration_ms < 0)}
    return runs, meta