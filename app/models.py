from sqlalchemy import Column, Integer, String, Float, Boolean, Date, Index
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

    __table_args__ = (
        Index("idx_close_date", "close_approach_date"),
    )

    def __repr__(self) -> str:
        return f"<Neo {self.neo_id} {self.name}>"

class Subscriber(Base):
    __tablename__ = "subscribers"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True)

    def __repr__(self) -> str:
        return f"<Subscriber {self.url}>"
