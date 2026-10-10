from __future__ import annotations
import json
import sys
from backend.models import RunDetail

try:
    import orjson as _orjson
except ImportError:  # fallback so tests pass without the new dep
    _orjson = None


def _loads_line(raw: bytes):
    if _orjson is not None:
        return _orjson.loads(raw)
    return json.loads(raw.decode("utf-8"))
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


# ---------------------------------------------------------------------------
# Streaming (no-DB, scales to ~1M rows): never retain run objects.
# Only retained state is id -> byte offset (~20MB per 1M rows).
# ---------------------------------------------------------------------------

SUMMARY_KEYS = (
    "id", "agent", "model", "status", "started_at", "ended_at",
    "duration_ms", "input_tokens", "output_tokens", "cost_usd",
    "prompt", "error", "tenant_id",
)


def build_offset_index(path: str) -> tuple[dict[str, int], list[str], int]:
    """Single streaming pass: map every live run id to its file byte offset.

    Duplicate ids keep the LAST offset (same rule as load_runs).
    Only parses the `id` field per line; never builds run objects.
    """
    offsets: dict[str, int] = {}
    duplicate_ids: list[str] = []
    seen: set[str] = set()
    skipped_lines = 0
    with open(path, "rb") as f:
        while True:
            off = f.tell()
            line = f.readline()
            if not line:
                break
            if not line.strip():
                continue
            try:
                raw = _loads_line(line)
            except Exception as e:
                skipped_lines += 1
                print(f"warn: skip offset {off}: {e}", file=sys.stderr)
                continue
            rid = raw.get("id") if isinstance(raw, dict) else None
            if not rid:
                skipped_lines += 1
                print(f"warn: skip offset {off}: missing id", file=sys.stderr)
                continue
            if rid in seen and rid not in duplicate_ids:
                duplicate_ids.append(rid)
                print(f"warn: duplicate id {rid}, keeping last", file=sys.stderr)
            seen.add(rid)
            offsets[rid] = off  # last wins; dict keeps first-insert position
    return offsets, sorted(duplicate_ids), skipped_lines


def read_run_at(path: str, offset: int) -> RunDetail:
    """Seek to one line and validate exactly one run (detail endpoint)."""
    with open(path, "rb") as f:
        f.seek(offset)
        line = f.readline()
    raw = _loads_line(line)
    return RunDetail.model_validate(raw)


def summarize_raw(raw: dict) -> dict:
    """Project a raw JSON dict to a RunSummary-shaped dict (no steps)."""
    return {
        "id": raw.get("id", ""),
        "agent": raw.get("agent", ""),
        "model": raw.get("model", ""),
        "status": raw.get("status", ""),
        "started_at": raw.get("started_at", ""),
        "ended_at": raw.get("ended_at"),
        "duration_ms": raw.get("duration_ms"),
        "input_tokens": raw.get("input_tokens", 0),
        "output_tokens": raw.get("output_tokens", 0),
        "cost_usd": raw.get("cost_usd"),
        "prompt": raw.get("prompt", ""),
        "error": raw.get("error"),
        "tenant_id": raw.get("tenant_id", ""),
    }


def iter_live_raw(path: str, offsets: dict[str, int]):
    """Yield (offset, raw dict) for live rows only, in file order.

    Stale duplicate occurrences are skipped via the offset check, so the
    keep-last rule holds without retaining any rows.
    """
    with open(path, "rb") as f:
        while True:
            off = f.tell()
            line = f.readline()
            if not line:
                break
            if not line.strip():
                continue
            try:
                raw = _loads_line(line)
            except Exception:
                continue
            if not isinstance(raw, dict):
                continue
            rid = raw.get("id")
            if not isinstance(rid, str) or offsets.get(rid) != off:
                continue  # stale duplicate, unknown, or missing id
            yield off, raw