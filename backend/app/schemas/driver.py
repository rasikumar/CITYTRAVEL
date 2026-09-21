from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DriverLogin(BaseModel):
    driver_id: str
    password: str

class DriverCreate(BaseModel):
    driver_id: str
    driver_name: str
    phone: str
    password: str
    photo: Optional[str] = "/assets/default-driver.png"
    shift_start: Optional[str] = "08:00"
    shift_end: Optional[str] = "16:00"
    lunch_start: Optional[str] = "12:30"
    lunch_end: Optional[str] = "13:00"

class DriverUpdate(BaseModel):
    driver_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    photo: Optional[str] = None
    shift_start: Optional[str] = None
    shift_end: Optional[str] = None
    lunch_start: Optional[str] = None
    lunch_end: Optional[str] = None

class DriverResponse(BaseModel):
    id: int
    driver_id: str
    driver_name: str
    phone: str
    photo: Optional[str]
    shift_start: Optional[str]
    shift_end: Optional[str]
    lunch_start: Optional[str]
    lunch_end: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class DriverProfileResponse(BaseModel):
    driver: DriverResponse
    assigned_bus: Optional[dict] = None
    assigned_route: Optional[dict] = None
    active_trip: Optional[dict] = None
