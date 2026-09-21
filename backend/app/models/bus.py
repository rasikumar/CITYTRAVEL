from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class Bus(Base):
    __tablename__ = "buses"

    id = Column(Integer, primary_key=True, index=True)
    bus_id = Column(String(50), unique=True, index=True, nullable=False)
    registration_number = Column(String(50), nullable=False)
    bus_name = Column(String(120), nullable=False)
    capacity = Column(Integer, default=50)
    
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="IDLE")  # IDLE, ACTIVE, MAINTENANCE
    
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    current_speed = Column(Float, default=0.0)
    last_telemetry_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    driver = relationship("Driver", back_populates="buses")
    route = relationship("Route", back_populates="buses")
    trips = relationship("Trip", back_populates="bus")
    tickets = relationship("Ticket", back_populates="bus")
