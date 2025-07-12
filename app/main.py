import asyncio
import time
from fastapi import FastAPI, Depends, Request, HTTPException, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse
from prometheus_client import (
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from .database import SessionLocal, engine
from . import models, schemas
from .services import fetch_neos, store_neos
from .scheduler import scheduler
from .events import event_queue
from datetime import datetime, date
import json

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])
templates = Jinja2Templates(directory="static")

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "http_status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
)

@app.on_event("startup")
async def startup_event():
    scheduler.start()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    method = request.method
    endpoint = request.url.path
    start_time = time.monotonic()
    response = await call_next(request)
    duration = time.monotonic() - start_time
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=response.status_code).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
    return response

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/neos")
async def get_neos(
    start_date: str | None = None,
    end_date: str | None = None,
    hazardous: str | None = None,
    db: Session = Depends(get_db),
):
    def parse_date(value: str) -> date:
        try:
            return date.fromisoformat(value)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date")

    start = parse_date(start_date) if start_date else None
    end = parse_date(end_date) if end_date else None

    if hazardous is not None:
        if hazardous.lower() in {"true", "1"}:
            hazard_bool = True
        elif hazardous.lower() in {"false", "0"}:
            hazard_bool = False
        else:
            raise HTTPException(status_code=400, detail="Invalid hazardous")
    else:
        hazard_bool = None

    q = db.query(models.Neo)
    if start:
        q = q.filter(models.Neo.close_approach_date >= start)
    if end:
        q = q.filter(models.Neo.close_approach_date <= end)
    if hazard_bool is not None:
        q = q.filter(models.Neo.hazardous == hazard_bool)
    neos = q.all()
    return [schemas.NeoRead.from_orm(n) for n in neos]

@app.get("/neos/{neo_id}")
async def get_neo(neo_id: int, db: Session = Depends(get_db)):
    n = db.query(models.Neo).filter(models.Neo.id == neo_id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Not Found")
    return schemas.NeoRead.from_orm(n)

@app.post("/subscribe", status_code=201)
async def subscribe(sub: schemas.SubscriberCreate, db: Session = Depends(get_db)):
    obj = models.Subscriber(url=sub.url)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return schemas.SubscriberRead.from_orm(obj)


@app.get("/subscribers")
async def get_subscribers(db: Session = Depends(get_db)):
    subs = db.query(models.Subscriber).all()
    return [schemas.SubscriberRead.from_orm(s) for s in subs]


@app.delete("/subscribers/{sub_id}", status_code=204)
async def delete_subscriber(sub_id: int, db: Session = Depends(get_db)):
    sub = db.query(models.Subscriber).filter(models.Subscriber.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Not Found")
    db.delete(sub)
    db.commit()
    return Response(status_code=204)

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


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
