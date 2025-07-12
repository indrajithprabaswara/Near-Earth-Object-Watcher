import os
os.environ['TEST_DB_URL'] = 'sqlite:///test.db'
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_neos_endpoint():
    resp = client.get("/neos")
    assert resp.status_code == 200
