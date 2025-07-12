import os
import pytest
from datetime import date

from app import services, models
from app.database import SessionLocal, engine
from app.events import event_queue

models.Base.metadata.create_all(bind=engine)

@pytest.mark.asyncio
async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_ingest_and_alert(client, monkeypatch):
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    while not event_queue.empty():
        event_queue.get_nowait()

    db = SessionLocal()
    try:
        db.add(models.Subscriber(url="http://example.com"))
        db.commit()
    finally:
        db.close()

    neos = [
        {
            "neo_id": "1",
            "name": "Test",
            "close_approach_date": date.today(),
            "diameter_km": 1.0,
            "velocity_km_s": 2.0,
            "miss_distance_au": 0.01,
            "hazardous": True,
        },
        {
            "neo_id": "2",
            "name": "Far",
            "close_approach_date": date.today(),
            "diameter_km": 1.0,
            "velocity_km_s": 2.0,
            "miss_distance_au": 0.2,
            "hazardous": False,
        },
    ]

    monkeypatch.setattr(services, "fetch_neos", lambda d: neos)
    import app.main as main_mod
    monkeypatch.setattr(main_mod, "fetch_neos", lambda d: neos)

    sent = []
    monkeypatch.setattr(services.slack_session, "post", lambda url, json, timeout: sent.append(url))
    monkeypatch.setattr(main_mod.BackgroundTasks, "add_task", lambda self, fn: fn())

    resp = await client.post("/ingest")
    assert resp.status_code == 200

    db = SessionLocal()
    try:
        objs = db.query(models.Neo).all()
        assert len(objs) == 2
    finally:
        db.close()

    assert event_queue.qsize() == 2
    assert sent == ["http://example.com"]


@pytest.mark.asyncio
async def test_neos_filters_and_errors(client):
    db = SessionLocal()
    try:
        db.add(models.Neo(
            neo_id="2",
            name="Two",
            close_approach_date=date.today(),
            diameter_km=1.0,
            velocity_km_s=1.0,
            miss_distance_au=0.5,
            hazardous=False,
        ))
        db.commit()
    finally:
        db.close()

    resp = await client.get("/neos", params={"start_date": "bad"})
    assert resp.status_code == 400

    resp = await client.get("/neos", params={"hazardous": "maybe"})
    assert resp.status_code == 400

    resp = await client.get("/neos", params={"hazardous": "false"})
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_get_neo_not_found(client):
    resp = await client.get("/neos/999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Not Found"


@pytest.mark.asyncio
async def test_subscriber_crud(client):
    resp = await client.post("/subscribe", json={"url": "http://example.com"})
    assert resp.status_code == 200
    sid = resp.json()["id"]

    resp = await client.get("/subscribers")
    assert resp.status_code == 200
    assert any(s["id"] == sid for s in resp.json())

    resp = await client.delete(f"/subscribers/{sid}")
    assert resp.status_code == 204

    resp = await client.delete(f"/subscribers/{sid}")
    assert resp.status_code == 404
