from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TicketPurchase(BaseModel):
    bus_id: str
    route_id: Optional[str] = None
    ticket_type: str  # Single, Return, Day Pass, Student
    payment_method: str  # Google Pay, PhonePe, Paytm, RuPay

class TicketResponse(BaseModel):
    id: int
    ticket_number: str
    passenger_id: int
    bus_id: Optional[int] = None
    bus_name: Optional[str] = None
    route_name: Optional[str] = None
    ticket_type: str
    fare: float
    status: str
    qr_code_data: str
    payment_provider: Optional[str] = None
    payment_status: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
