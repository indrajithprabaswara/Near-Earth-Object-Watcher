import asyncio
from datetime import datetime, date

import pytest

from apscheduler.triggers.interval import IntervalTrigger

from app import services, models
from app.database import engine
from app import scheduler as scheduler_mod
from app.scheduler import scheduler, ingest_once
from app.events import event_queue


@pytest.mark.asyncio
async def test_scheduler_config():
    jobs = scheduler.get_jobs()
    assert len(jobs) == 1
    job = jobs[0]
    assert isinstance(job.trigger, IntervalTrigger)
    assert job.trigger.interval.total_seconds() == 3600


@pytest.mark.asyncio
async def test_scheduler_runs(monkeypatch):
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    event_queue.put_nowait({})
    while not event_queue.empty():
        event_queue.get_nowait()

    def fake_fetch(_):
        return [{
            "neo_id": "99",
            "name": "Sched",
            "close_approach_date": date.today(),
            "diameter_km": 1.0,
            "velocity_km_s": 1.0,
            "miss_distance_au": 0.04,
            "hazardous": True,
        }]
    fake_fetch(None)

    monkeypatch.setattr(services, "fetch_neos", fake_fetch)
    monkeypatch.setattr(services.slack_session, "post", lambda *a, **k: None)

    scheduler.remove_all_jobs()
    scheduler.add_job(ingest_once, IntervalTrigger(seconds=0.1), next_run_time=datetime.utcnow())
    scheduler.start()
    await asyncio.sleep(0.2)
    scheduler.shutdown(wait=False)

    assert not event_queue.empty()


@pytest.mark.asyncio
async def test_scheduled_ingest(monkeypatch):
    called = {"c": False}

    async def fake_ingest_once():
        called["c"] = True

    monkeypatch.setattr(scheduler_mod, "ingest_once", fake_ingest_once)
    await scheduler_mod.scheduled_ingest()
    assert called["c"]


@pytest.mark.asyncio
async def test_startup_event(monkeypatch):
    from app.main import startup_event

    hit = {"x": False}
    monkeypatch.setattr(scheduler_mod.scheduler, "start", lambda: hit.update(x=True))
    await startup_event()
    assert hit["x"]
