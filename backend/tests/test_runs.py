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
