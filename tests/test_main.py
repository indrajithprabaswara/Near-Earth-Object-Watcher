import os
os.environ['TEST_DB_URL'] = 'sqlite:///test.db'
from fastapi.testclient import TestClient
from app.main import app
from app import services

client = TestClient(app)

def test_root():
    resp = client.get("/")
    assert resp.status_code == 200


def test_ingest_and_alert(monkeypatch):
    called = {}

    def fake_fetch(date):
        return [
            {
                "neo_id": "1",
                "name": "Test",
                "close_approach_date": date.date(),
                "diameter_km": 1.0,
                "velocity_km_s": 2.0,
                "miss_distance_au": 0.01,
                "hazardous": True,
            }
        ]

    def fake_slack(url, json, timeout):
        called["hit"] = True

    monkeypatch.setattr(services, "fetch_neos", fake_fetch)
    monkeypatch.setattr(services.slack_session, "post", fake_slack)
    import app.main as main_mod
    monkeypatch.setattr(main_mod, "fetch_neos", fake_fetch)

    resp = client.post("/ingest")
    assert resp.status_code == 200
    assert called.get("hit")
