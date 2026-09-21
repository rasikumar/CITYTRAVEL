from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class TravelUpdate(Base):
    __tablename__ = "travel_updates"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    category = Column(String(50), default="Advisory")  # Festival advisory, Route diversion, Service timing, Public transport
    summary = Column(String(300), nullable=False)
    severity = Column(String(20), default="info")  # info, warning, alert
    published_at = Column(DateTime, default=datetime.utcnow)
