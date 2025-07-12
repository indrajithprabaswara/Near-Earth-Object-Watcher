from pydantic import BaseModel
from datetime import date

class NeoBase(BaseModel):
    neo_id: str
    name: str
    close_approach_date: date
    diameter_km: float
    velocity_km_s: float
    miss_distance_au: float
    hazardous: bool

class NeoCreate(NeoBase):
    pass

class NeoRead(NeoBase):
    id: int

    class Config:
        orm_mode = True

class SubscriberCreate(BaseModel):
    url: str

class SubscriberRead(SubscriberCreate):
    id: int

    class Config:
        orm_mode = True
