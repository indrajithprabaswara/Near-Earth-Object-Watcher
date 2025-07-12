import asyncio
from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse
from .database import SessionLocal, engine
from . import models, schemas
from .services import fetch_neos, store_neos
from .scheduler import scheduler
from datetime import datetime
import json

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])
templates = Jinja2Templates(directory="static")

@app.on_event("startup")
async def startup_event():
    scheduler.start()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/neos")
async def get_neos(start_date: str = None, end_date: str = None, hazardous: bool = None, db: Session = Depends(get_db)):
    q = db.query(models.Neo)
    if start_date:
        q = q.filter(models.Neo.close_approach_date >= start_date)
    if end_date:
        q = q.filter(models.Neo.close_approach_date <= end_date)
    if hazardous is not None:
        q = q.filter(models.Neo.hazardous == hazardous)
    return [schemas.NeoRead.from_orm(n) for n in q.all()]

@app.get("/neos/{neo_id}")
async def get_neo(neo_id: int, db: Session = Depends(get_db)):
    n = db.query(models.Neo).filter(models.Neo.id == neo_id).first()
    if not n:
        return {"error": "not found"}
    return schemas.NeoRead.from_orm(n)

@app.post("/subscribe")
async def subscribe(sub: schemas.SubscriberCreate, db: Session = Depends(get_db)):
    obj = models.Subscriber(url=sub.url)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return schemas.SubscriberRead.from_orm(obj)

event_queue: asyncio.Queue = asyncio.Queue()

@app.get("/stream/neos")
async def stream_neos(request: Request):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            try:
                data = await asyncio.wait_for(event_queue.get(), timeout=15)
                yield {"event": "message", "data": json.dumps(data)}
            except asyncio.TimeoutError:
                yield {"event": "heartbeat", "data": "ping"}
    return EventSourceResponse(event_generator())

@app.post("/ingest")
async def ingest(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    def task():
        neos = fetch_neos(datetime.utcnow())
        stored = store_neos(db, neos)
        for n in stored:
            event_queue.put_nowait(schemas.NeoRead.from_orm(n).dict())
    background_tasks.add_task(task)
    return {"status": "started"}
