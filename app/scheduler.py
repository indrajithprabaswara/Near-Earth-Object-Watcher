from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from .database import SessionLocal
from .services import fetch_neos, store_neos
from . import schemas
from .events import event_queue

scheduler = AsyncIOScheduler()

async def ingest_once():
    db = SessionLocal()
    try:
        neos = fetch_neos(datetime.utcnow())
        stored = store_neos(db, neos)
        for n in stored:
            event_queue.put_nowait(schemas.NeoRead.from_orm(n).dict())
    finally:
        db.close()

@scheduler.scheduled_job(IntervalTrigger(hours=1))
async def scheduled_ingest():
    await ingest_once()
