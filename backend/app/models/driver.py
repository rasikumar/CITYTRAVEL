from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(String(50), unique=True, index=True, nullable=False)
    driver_name = Column(String(120), nullable=False)
    phone = Column(String(20), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    photo = Column(String(255), nullable=True, default="/assets/default-driver.png")
    shift_start = Column(String(10), default="08:00")
    shift_end = Column(String(10), default="16:00")
    lunch_start = Column(String(10), default="12:30")
    lunch_end = Column(String(10), default="13:00")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    buses = relationship("Bus", back_populates="driver")
    trips = relationship("Trip", back_populates="driver")
