from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import TravelUpdate

router = APIRouter(prefix="/api/travel-updates", tags=["Travel Updates"])

@router.get("")
def get_travel_updates(db: Session = Depends(get_db)):
    updates = db.query(TravelUpdate).order_by(TravelUpdate.id.desc()).limit(10).all()
    return [
        {
            "id": u.id,
            "title": u.title,
            "category": u.category,
            "summary": u.summary,
            "severity": u.severity,
            "published_at": u.published_at.strftime("%b %d, %H:%M") if u.published_at else ""
        }
        for u in updates
    ]
