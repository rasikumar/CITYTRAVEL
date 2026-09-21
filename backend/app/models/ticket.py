from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(50), unique=True, index=True, nullable=False)
    passenger_id = Column(Integer, ForeignKey("passengers.id", ondelete="CASCADE"), nullable=False)
    bus_id = Column(Integer, ForeignKey("buses.id", ondelete="SET NULL"), nullable=True)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="SET NULL"), nullable=True)
    
    ticket_type = Column(String(50), nullable=False)  # Single, Return, Day Pass, Student
    fare = Column(Float, nullable=False)
    status = Column(String(50), default="ACTIVE")    # ACTIVE, USED, EXPIRED
    qr_code_data = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    passenger = relationship("Passenger", back_populates="tickets")
    bus = relationship("Bus", back_populates="tickets")
    payment = relationship("Payment", back_populates="ticket", uselist=False, cascade="all, delete-orphan")
