from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TelemetryIngest(BaseModel):
    driver_id: str
    bus_id: str
    trip_id: str
    route_id: str
    latitude: float
    longitude: float
    speed: Optional[float] = 0.0
    accuracy: Optional[float] = 10.0
    timestamp: Optional[str] = None
    source: Optional[str] = "phone_gps"

class TelemetryResponse(BaseModel):
    id: int
    trip_id: int
    bus_id: int
    driver_id: int
    route_id: int
    latitude: float
    longitude: float
    speed: float
    accuracy: float
    source: str
    timestamp: datetime

    class Config:
        from_attributes = True

class WebSocketTelemetryBroadcast(BaseModel):
    bus_id: str
    route_id: str
    trip_id: str
    latitude: float
    longitude: float
    speed: float
    accuracy: float
    next_stop: Optional[str] = None
    eta: Optional[str] = None
    trip_status: str = "ACTIVE"
    delay_reason: Optional[str] = None
    telemetry_source: str = "phone_gps"
    timestamp: str
