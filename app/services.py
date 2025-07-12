import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from datetime import datetime
from sqlalchemy.orm import Session
from .config import NASA_API_KEY, SLACK_WEBHOOK_URL
from . import models

API_URL = "https://api.nasa.gov/neo/rest/v1/feed"

# session with retry for Slack notifications
slack_session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
slack_session.mount("https://", HTTPAdapter(max_retries=retries))

def fetch_neos(date: datetime):
    params = {
        "start_date": date.strftime("%Y-%m-%d"),
        "end_date": date.strftime("%Y-%m-%d"),
        "api_key": NASA_API_KEY,
    }
    resp = requests.get(API_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    neos = []
    for item in data.get("near_earth_objects", {}).get(params["start_date"], []):
        neo = {
            "neo_id": item["id"],
            "name": item["name"],
            "close_approach_date": datetime.strptime(
                item["close_approach_data"][0]["close_approach_date"], "%Y-%m-%d"
            ).date(),
            "diameter_km": item["estimated_diameter"]["kilometers"]["estimated_diameter_max"],
            "velocity_km_s": float(item["close_approach_data"][0]["relative_velocity"]["kilometers_per_second"]),
            "miss_distance_au": float(item["close_approach_data"][0]["miss_distance"]["astronomical"]),
            "hazardous": item["is_potentially_hazardous_asteroid"],
        }
        neos.append(neo)
    return neos

def store_neos(db: Session, neos):
    stored = []
    for data in neos:
        existing = db.query(models.Neo).filter_by(neo_id=data["neo_id"]).first()
        if existing:
            continue
        obj = models.Neo(**data)
        db.add(obj)
        stored.append(obj)
    db.commit()
    for obj in stored:
        if obj.miss_distance_au < 0.05:
            slack_session.post(
                SLACK_WEBHOOK_URL,
                json={"text": f"Close NEO: {obj.name} at {obj.miss_distance_au} AU"},
                timeout=5,
            )
    return stored
