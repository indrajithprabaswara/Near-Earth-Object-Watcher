import os
from datetime import datetime, date

from app import services, models
from app.database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)


def test_fetch_neos(monkeypatch):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    payload = {
        "near_earth_objects": {
            today: [
                {
                    "id": "42",
                    "name": "Apophis",
                    "close_approach_data": [
                        {
                            "close_approach_date": today,
                            "relative_velocity": {"kilometers_per_second": "1"},
                            "miss_distance": {"astronomical": "0.04"},
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
        assert params["start_date"] == today
        return Resp()

    monkeypatch.setattr(services.httpx, "get", fake_get)
    result = services.fetch_neos(datetime.utcnow())
    assert result == [
        {
            "neo_id": "42",
            "name": "Apophis",
            "close_approach_date": date.fromisoformat(today),
            "diameter_km": 1,
            "velocity_km_s": 1.0,
            "miss_distance_au": 0.04,
            "hazardous": False,
        }
    ]


def test_store_neos(monkeypatch):
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.add(models.Subscriber(url="http://example.com"))
        db.commit()
    finally:
        db.close()

    sent = []
    calls = {"n": 0}

    def fake_post(url, json, timeout):
        calls["n"] += 1
        if calls["n"] == 1:
            raise Exception("boom")
        sent.append(url)

    monkeypatch.setattr(services.slack_session, "post", fake_post)

    db = SessionLocal()
    try:
        neos = [
            {
                "neo_id": "1",
                "name": "One",
                "close_approach_date": date.today(),
                "diameter_km": 1.0,
                "velocity_km_s": 1.0,
                "miss_distance_au": 0.04,
                "hazardous": True,
            },
            {
                "neo_id": "2",
                "name": "Two",
                "close_approach_date": date.today(),
                "diameter_km": 1.0,
                "velocity_km_s": 1.0,
                "miss_distance_au": 0.5,
                "hazardous": False,
            },
        ]
        stored = services.store_neos(db, neos)
        assert len(stored) == 2
        assert sent == ["http://example.com"]
        assert calls["n"] == 2

        again = services.store_neos(db, neos)
        assert len(again) == 0
    finally:
        db.close()

def test_store_neos_retries(monkeypatch):
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.add(models.Subscriber(url="http://example.com"))
        db.commit()
    finally:
        db.close()

    calls = {"n": 0}
    def always_fail(url, json, timeout):
        calls["n"] += 1
        raise Exception("boom")

    monkeypatch.setattr(services.slack_session, "post", always_fail)

    db = SessionLocal()
    try:
        neos = [
            {
                "neo_id": "x",
                "name": "Fail",
                "close_approach_date": date.today(),
                "diameter_km": 1.0,
                "velocity_km_s": 1.0,
                "miss_distance_au": 0.04,
                "hazardous": True,
            }
        ]
        services.store_neos(db, neos)
        assert calls["n"] == 3
    finally:
        db.close()


def test_model_repr():
    n = models.Neo(
        neo_id="r",
        name="Rep",
        close_approach_date=date.today(),
        diameter_km=1.0,
        velocity_km_s=1.0,
        miss_distance_au=0.1,
        hazardous=False,
    )
    s = models.Subscriber(url="http://example.com")
    assert "<Neo r Rep>" == repr(n)
    assert "<Subscriber http://example.com>" == repr(s)
