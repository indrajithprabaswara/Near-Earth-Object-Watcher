import os
os.environ['TEST_DB_URL'] = 'sqlite:///test.db'
import pytest
from httpx import AsyncClient
from app.main import app, scheduler, event_queue
from app import models
from app.database import engine


import pytest_asyncio


@pytest_asyncio.fixture
async def client(monkeypatch):
    monkeypatch.setattr(scheduler, "start", lambda: None)
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    # reset queue between tests
    while not event_queue.empty():
        event_queue.get_nowait()
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
