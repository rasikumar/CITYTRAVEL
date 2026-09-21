from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DelayCreate(BaseModel):
    trip_id: str
    bus_id: str
    driver_id: str
    reason: str
    note: Optional[str] = None

class DelayResponse(BaseModel):
    id: int
    trip_id: int
    bus_id: int
    driver_id: int
    reason: str
    note: Optional[str]
    reported_at: datetime

    class Config:
        from_attributes = True
