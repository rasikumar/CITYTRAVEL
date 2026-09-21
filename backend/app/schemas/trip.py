from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TripStart(BaseModel):
    driver_id: str
    bus_id: str
    route_id: str

class TripEnd(BaseModel):
    trip_id: str

class TripResponse(BaseModel):
    id: int
    trip_id: str
    bus_id: int
    driver_id: int
    route_id: int
    bus_name: Optional[str] = None
    route_name: Optional[str] = None
    driver_name: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
