from fastapi.testclient import TestClient
from backend.app import app
client = TestClient(app)
def test_explain_streams_and_404():
    r = client.post("/api/runs/run_0089/explain")
    assert r.status_code == 200
    text = r.text
    assert "kpi-analyst" in text
    assert "SchemaMismatch" in text
    assert len(text) > 100
    r2 = client.post("/api/runs/nope/explain")
    assert r2.status_code == 404
