from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from .database import SessionLocal
from .services import fetch_neos, store_neos

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=0)
async def daily_ingest():
    db = SessionLocal()
    try:
        neos = fetch_neos(datetime.utcnow())
        store_neos(db, neos)
    finally:
        db.close()
