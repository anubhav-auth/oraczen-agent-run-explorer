import os
from backend.loader import load_runs
from backend.models import RunDetail, RunSummary, Step


DATA = os.path.join(os.path.dirname(__file__), "../../data/runs.jsonl")


def test_models_import():
    assert RunDetail is not None
    assert RunSummary is not None
    assert Step is not None


def test_loader_dedupes_keep_last():
    runs, meta = load_runs(DATA)
    assert len(runs) == 200
    by_id = {r.id: r for r in runs}
    assert by_id["run_0031"].status == "running"
    assert "run_0031" in meta["duplicate_ids"]


def test_loader_preserves_bad_values():
    runs, _ = load_runs(DATA)
    by_id = {r.id: r for r in runs}
    assert by_id["run_0064"].duration_ms == -4000
    nulls = sorted(r.id for r in runs if r.cost_usd is None)
    assert nulls == ["run_0008", "run_0042", "run_0153"]
    assert by_id["run_0089"].steps == []
