from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.stop import StopResponse

class RouteStopItem(BaseModel):
    stop_id: str
    stop_name: str
    latitude: float
    longitude: float
    sequence: int
    scheduled_arrival_time: Optional[str] = "08:00"
    dwell_time_minutes: Optional[int] = 3

class RouteStopCreate(BaseModel):
    stop_id: Optional[str] = None
    stop_name: str
    latitude: float
    longitude: float
    sequence: int
    scheduled_arrival_time: Optional[str] = "08:00"
    dwell_time_minutes: Optional[int] = 3

class RouteBase(BaseModel):
    route_id: str
    route_name: str
    direction: Optional[str] = "Outbound"
    is_active: Optional[bool] = True

class RouteCreate(RouteBase):
    stops: Optional[List[RouteStopCreate]] = []

class RouteUpdate(BaseModel):
    route_name: Optional[str] = None
    direction: Optional[str] = None
    is_active: Optional[bool] = None

class RouteResponse(RouteBase):
    id: int
    created_at: datetime
    stops: List[RouteStopItem] = []

    class Config:
        from_attributes = True
