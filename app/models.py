from sqlalchemy import Column, Integer, String, Float, Boolean, Date
from .database import Base

class Neo(Base):
    __tablename__ = "neos"
    id = Column(Integer, primary_key=True, index=True)
    neo_id = Column(String, unique=True, index=True)
    name = Column(String)
    close_approach_date = Column(Date)
    diameter_km = Column(Float)
    velocity_km_s = Column(Float)
    miss_distance_au = Column(Float)
    hazardous = Column(Boolean)

class Subscriber(Base):
    __tablename__ = "subscribers"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True)
