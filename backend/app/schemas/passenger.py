from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class PassengerRegister(BaseModel):
    full_name: str
    phone: str
    email: EmailStr
    password: str
    confirm_password: str

class PassengerLogin(BaseModel):
    username: str  # Can be phone or email
    password: str

class PassengerResponse(BaseModel):
    id: int
    full_name: str
    phone: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str = "passenger"
    user: Optional[dict] = None
