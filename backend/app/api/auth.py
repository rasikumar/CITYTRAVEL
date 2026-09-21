from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Passenger, Driver
from app.schemas.passenger import PassengerRegister, PassengerLogin, Token
from app.schemas.driver import DriverLogin
from app.auth.security import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/passenger/register", response_model=Token)
def register_passenger(payload: PassengerRegister, db: Session = Depends(get_db)):
    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password and confirmation do not match"
        )
    
    # Check if email or phone already exists
    if db.query(Passenger).filter(Passenger.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )
    if db.query(Passenger).filter(Passenger.phone == payload.phone).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number is already registered"
        )

    new_passenger = Passenger(
        full_name=payload.full_name,
        phone=payload.phone,
        email=payload.email,
        hashed_password=get_password_hash(payload.password)
    )
    db.add(new_passenger)
    db.commit()
    db.refresh(new_passenger)

    # Automatically generate access token
    access_token = create_access_token(subject=str(new_passenger.id), role="passenger")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": "passenger",
        "user": {
            "id": new_passenger.id,
            "full_name": new_passenger.full_name,
            "email": new_passenger.email,
            "phone": new_passenger.phone
        }
    }

@router.post("/passenger/login", response_model=Token)
def login_passenger(payload: PassengerLogin, db: Session = Depends(get_db)):
    # Support login with either email or phone
    passenger = db.query(Passenger).filter(
        (Passenger.email == payload.username) | (Passenger.phone == payload.username)
    ).first()

    if not passenger or not verify_password(payload.password, passenger.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/phone or password"
        )

    access_token = create_access_token(subject=str(passenger.id), role="passenger")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": "passenger",
        "user": {
            "id": passenger.id,
            "full_name": passenger.full_name,
            "email": passenger.email,
            "phone": passenger.phone
        }
    }

@router.post("/passenger/logout")
def logout_passenger():
    return {"message": "Passenger logged out successfully"}

@router.post("/driver/login", response_model=Token)
def login_driver(payload: DriverLogin, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.driver_id == payload.driver_id).first()

    if not driver or not verify_password(payload.password, driver.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Driver ID or password"
        )

    access_token = create_access_token(subject=str(driver.id), role="driver")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": "driver",
        "user": {
            "id": driver.id,
            "driver_id": driver.driver_id,
            "driver_name": driver.driver_name,
            "phone": driver.phone,
            "photo": driver.photo
        }
    }

@router.post("/driver/logout")
def logout_driver():
    return {"message": "Driver logged out successfully"}
