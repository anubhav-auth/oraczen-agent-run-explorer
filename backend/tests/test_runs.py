from fastapi.testclient import TestClient
from backend.app import app
client = TestClient(app)
def test_two_filters_compose():
    r = client.get("/api/runs", params=[("agent", "email-drafter"), ("status", "succeeded")])
    assert r.status_code == 200
    body = r.json()
    assert body["total"] > 0
    for item in body["items"]:
        assert item["agent"] == "email-drafter"
        assert item["status"] == "succeeded"
    assert "steps" not in body["items"][0]
def test_search_and_sort_nulls_last():
    r = client.get("/api/runs", params={"q": "liability caps", "sort": "duration_ms", "order": "asc"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    durs = [i["duration_ms"] for i in body["items"]]
    non_null = [d for d in durs if d is not None]
    assert non_null == sorted(non_null)


def test_detail_includes_steps_and_404():
    r = client.get("/api/runs/run_0089")
    assert r.status_code == 200
    assert r.json()["id"] == "run_0089"
    assert r.json()["steps"] == []
    r2 = client.get("/api/runs/run_0031")
    assert r2.status_code == 200
    assert r2.json()["status"] == "running"
    r3 = client.get("/api/runs/does_not_exist")
    assert r3.status_code == 404


def test_date_only_range_behaves():
    # date-only bounds (what <input type="date"> sends) must not 500:
    # from-bound is start of day, to-bound is end of day, both UTC.
    r = client.get("/api/runs", params={"started_from": "2026-08-01", "started_to": "2026-08-10", "page_size": 100})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 38
    for item in body["items"]:
        assert "2026-08-01" <= item["started_at"][:10] <= "2026-08-10"
    bad = client.get("/api/runs", params={"started_from": "garbage"})
    assert bad.status_code == 422
