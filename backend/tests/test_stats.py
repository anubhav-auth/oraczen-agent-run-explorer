from fastapi.testclient import TestClient
from backend.app import app
client = TestClient(app)
def test_stats_hand_computed():
    r = client.get("/api/stats")
    assert r.status_code == 200
    s = r.json()
    assert s["total"] == 200
    assert s["unpriced_count"] == 3
    assert abs(s["success_rate"] - 139 / 191) < 1e-6
    assert s["median_duration_ms"] == 23593.0
    assert s["p95_duration_ms"] == 41530
    assert "run_0031" in s["meta"]["duplicate_ids"]
    assert "run_0064" in s["meta"]["excluded_negative"]
    assert s["cost_by_agent"]["email-drafter"] > 0
    days = {d["date"]: d["count"] for d in s["runs_per_day"]}
    assert "2026-07-20" in days and "2026-08-31" in days
