from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Stop
from app.schemas.stop import StopResponse

router = APIRouter(prefix="/api/stops", tags=["Stops"])

@router.get("", response_model=List[StopResponse])
def get_all_stops(db: Session = Depends(get_db)):
    stops = db.query(Stop).order_by(Stop.stop_name).all()
    return stops

@router.get("/{id}", response_model=StopResponse)
def get_stop_by_id(id: int, db: Session = Depends(get_db)):
    stop = db.query(Stop).filter(Stop.id == id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")
    return stop
