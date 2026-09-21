from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class DelayReport(Base):
    __tablename__ = "delay_reports"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    bus_id = Column(Integer, ForeignKey("buses.id", ondelete="CASCADE"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False)
    
    reason = Column(String(100), nullable=False)
    note = Column(String(255), nullable=True)
    reported_at = Column(DateTime, default=datetime.utcnow)

    trip = relationship("Trip", back_populates="delays")
