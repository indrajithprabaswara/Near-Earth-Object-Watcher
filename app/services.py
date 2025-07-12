import os
import time
import httpx
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List
from .config import NASA_API_KEY
from . import models

API_URL = "https://api.nasa.gov/neo/rest/v1/feed"

# session with retry for Slack notifications
slack_session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
slack_session.mount("https://", HTTPAdapter(max_retries=retries))

def fetch_neos(date: datetime) -> List[dict]:
    """Fetch NEO data for a single day from NASA."""

    date_str = date.strftime("%Y-%m-%d")
    params = {
        "start_date": date_str,
        "end_date": date_str,
        "api_key": os.getenv("NASA_API_KEY", NASA_API_KEY),
    }

    resp = httpx.get(API_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    neos: List[dict] = []
    for item in data.get("near_earth_objects", {}).get(date_str, []):
        approach = item["close_approach_data"][0]
        neo = {
            "neo_id": item["id"],
            "name": item["name"],
            "close_approach_date": datetime.strptime(
                approach["close_approach_date"], "%Y-%m-%d"
            ).date(),
            "diameter_km": item["estimated_diameter"]["kilometers"][
                "estimated_diameter_max"
            ],
            "velocity_km_s": float(
                approach["relative_velocity"]["kilometers_per_second"]
            ),
            "miss_distance_au": float(approach["miss_distance"]["astronomical"]),
            "hazardous": item["is_potentially_hazardous_asteroid"],
        }
        neos.append(neo)
    return neos

def store_neos(db: Session, neos: List[dict]) -> List[models.Neo]:
    """Insert new NEOs and notify subscribers about close approaches."""

    stored: List[models.Neo] = []
    for data in neos:
        existing = db.query(models.Neo).filter_by(neo_id=data["neo_id"]).first()
        if existing:
            continue
        obj = models.Neo(**data)
        db.add(obj)
        stored.append(obj)

    db.commit()
    for obj in stored:
        db.refresh(obj)

    subscribers = db.query(models.Subscriber).all()
    for obj in stored:
        if obj.miss_distance_au < 0.05:
            payload = {
                "neo_id": obj.neo_id,
                "name": obj.name,
                "close_approach_date": obj.close_approach_date,
                "diameter_km": obj.diameter_km,
                "velocity_km_s": obj.velocity_km_s,
                "miss_distance_au": obj.miss_distance_au,
                "hazardous": obj.hazardous,
            }
            for sub in subscribers:
                delay = 1.0
                for attempt in range(3):
                    try:
                        slack_session.post(sub.url, json=payload, timeout=5)
                        break
                    except Exception:
                        if attempt == 2:
                            break
                        time.sleep(delay)
                        delay *= 2
    return stored
