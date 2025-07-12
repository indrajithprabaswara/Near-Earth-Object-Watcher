import os
import asyncio
import pytest
from datetime import date
import json

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
    event_queue.put_nowait({})
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
    assert resp.status_code == 201
    sid = resp.json()["id"]

    resp = await client.get("/subscribers")
    assert resp.status_code == 200
    assert any(s["id"] == sid for s in resp.json())

    resp = await client.delete(f"/subscribers/{sid}")
    assert resp.status_code == 204

    resp = await client.delete(f"/subscribers/{sid}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_neo_and_filters_success(client):
    today = date.today()
    db = SessionLocal()
    try:
        neo = models.Neo(
            neo_id="3",
            name="Three",
            close_approach_date=today,
            diameter_km=1.0,
            velocity_km_s=1.0,
            miss_distance_au=0.04,
            hazardous=True,
        )
        db.add(neo)
        db.commit()
        db.refresh(neo)
        nid = neo.id
    finally:
        db.close()

    params = {
        "start_date": today.isoformat(),
        "end_date": today.isoformat(),
        "hazardous": "true",
    }
    resp = await client.get("/neos", params=params)
    assert resp.status_code == 200
    assert any(n["id"] == nid for n in resp.json())

    resp = await client.get("/neos")
    assert resp.status_code == 200

    resp = await client.get(f"/neos/{nid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == nid


@pytest.mark.asyncio
async def test_stream_neos(monkeypatch):
    from app.main import stream_neos

    payload = {"hello": "world"}
    event_queue.put_nowait(payload)

    class Req:
        def __init__(self):
            self.calls = 0
        async def is_disconnected(self):
            self.calls += 1
            return self.calls > 1

    resp = await stream_neos(Req())
    gen = resp.body_iterator
    event = await gen.__anext__()
    assert json.loads(event["data"]) == payload
    with pytest.raises(StopAsyncIteration):
        await gen.__anext__()


@pytest.mark.asyncio
async def test_stream_neos_heartbeat(monkeypatch):
    from app.main import stream_neos

    async def fake_wait_for(coro, timeout):
        coro.close()
        raise asyncio.TimeoutError

    monkeypatch.setattr(asyncio, "wait_for", fake_wait_for)

    class Req:
        def __init__(self):
            self.calls = 0
        async def is_disconnected(self):
            self.calls += 1
            return self.calls > 1

    resp = await stream_neos(Req())
    gen = resp.body_iterator
    event = await gen.__anext__()
    assert event["data"] == "ping"
    with pytest.raises(StopAsyncIteration):
        await gen.__anext__()
