from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class StopBase(BaseModel):
    stop_id: str
    stop_name: str
    latitude: float
    longitude: float

class StopCreate(StopBase):
    pass

class StopUpdate(BaseModel):
    stop_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class StopResponse(StopBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
