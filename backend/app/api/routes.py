from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Route, RouteStop, Stop, Bus
from app.schemas.route import RouteResponse, RouteStopItem
from app.services.distance import haversine_distance

router = APIRouter(prefix="/api/routes", tags=["Routes"])

def serialize_route(route: Route) -> dict:
    stops_list = []
    # Route stops are ordered by sequence
    for rs in route.route_stops:
        if rs.stop:
            stops_list.append({
                "stop_id": rs.stop.stop_id,
                "stop_name": rs.stop.stop_name,
                "latitude": rs.stop.latitude,
                "longitude": rs.stop.longitude,
                "sequence": rs.sequence,
                "scheduled_arrival_time": rs.scheduled_arrival_time,
                "dwell_time_minutes": rs.dwell_time_minutes,
            })
    return {
        "id": route.id,
        "route_id": route.route_id,
        "route_name": route.route_name,
        "direction": route.direction,
        "is_active": route.is_active,
        "created_at": route.created_at,
        "stops": stops_list
    }

@router.get("", response_model=List[RouteResponse])
def get_routes(db: Session = Depends(get_db)):
    routes = db.query(Route).filter(Route.is_active == True).all()
    return [serialize_route(r) for r in routes]

@router.get("/nearby")
def get_nearby_routes(
    lat: float = Query(..., description="Passenger latitude"),
    lon: float = Query(..., description="Passenger longitude"),
    db: Session = Depends(get_db)
):
    routes = db.query(Route).filter(Route.is_active == True).all()
    nearby = []
    
    for r in routes:
        min_dist = float("inf")
        closest_stop = None
        for rs in r.route_stops:
            if rs.stop:
                d = haversine_distance(lat, lon, rs.stop.latitude, rs.stop.longitude)
                if d < min_dist:
                    min_dist = d
                    closest_stop = rs.stop.stop_name
        
        serialized = serialize_route(r)
        serialized["distance_from_passenger_km"] = round(min_dist, 2)
        serialized["closest_stop"] = closest_stop
        nearby.append(serialized)
        
    nearby.sort(key=lambda x: x["distance_from_passenger_km"])
    return nearby

@router.get("/{id}", response_model=RouteResponse)
def get_route_by_id(id: int, db: Session = Depends(get_db)):
    route = db.query(Route).filter(Route.id == id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return serialize_route(route)
