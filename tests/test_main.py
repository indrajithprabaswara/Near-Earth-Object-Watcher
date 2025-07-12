import os
os.environ['TEST_DB_URL'] = 'sqlite:///test.db'
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
