import pytest
from datetime import datetime, date
from app import services, models
from app.database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)


def sample_neos():
    return [
        {
            "neo_id": "10",
            "name": "A",
            "close_approach_date": date.today(),
            "diameter_km": 1.0,
            "velocity_km_s": 1.0,
            "miss_distance_au": 0.04,
            "hazardous": True,
        }
    ]


def test_store_neos(monkeypatch):
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    called = {}

    def fake_post(url, json, timeout):
        called["hit"] = True

    monkeypatch.setattr(services.slack_session, "post", fake_post)

    db = SessionLocal()
    try:
        stored = services.store_neos(db, sample_neos())
        assert len(stored) == 1
        assert called.get("hit")
        again = services.store_neos(db, sample_neos())
        assert len(again) == 0
    finally:
        db.close()


def test_fetch_neos(monkeypatch):
    payload = {
        "near_earth_objects": {
            datetime.utcnow().strftime("%Y-%m-%d"): [
                {
                    "id": "10",
                    "name": "A",
                    "close_approach_data": [
                        {
                            "close_approach_date": date.today().strftime("%Y-%m-%d"),
                            "relative_velocity": {"kilometers_per_second": "1"},
                            "miss_distance": {"astronomical": "0.1"},
                        }
                    ],
                    "estimated_diameter": {"kilometers": {"estimated_diameter_max": 1}},
                    "is_potentially_hazardous_asteroid": False,
                }
            ]
        }
    }

    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return payload

    def fake_get(url, params, timeout):
        return Resp()

    monkeypatch.setattr(services.requests, "get", fake_get)
    result = services.fetch_neos(datetime.utcnow())
    assert result[0]["neo_id"] == "10"
