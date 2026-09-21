from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BusBase(BaseModel):
    bus_id: str
    registration_number: str
    bus_name: str
    capacity: Optional[int] = 50
    driver_id: Optional[int] = None
    route_id: Optional[int] = None

class BusCreate(BusBase):
    pass

class BusUpdate(BaseModel):
    registration_number: Optional[str] = None
    bus_name: Optional[str] = None
    capacity: Optional[int] = None
    driver_id: Optional[int] = None
    route_id: Optional[int] = None
    status: Optional[str] = None

class BusResponse(BusBase):
    id: int
    status: str
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    current_speed: Optional[float] = 0.0
    last_telemetry_at: Optional[datetime] = None
    created_at: datetime
    
    # Nested information
    driver_name: Optional[str] = None
    route_name: Optional[str] = None
    next_stop: Optional[str] = None
    eta: Optional[str] = None
    delay_reason: Optional[str] = None

    class Config:
        from_attributes = True
