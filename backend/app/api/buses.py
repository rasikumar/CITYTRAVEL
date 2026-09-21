from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.database import get_db
from app.models import Bus, Route, Stop, RouteStop, Trip, DelayReport
from app.schemas.bus import BusResponse
from app.services.eta import ETAEngine

router = APIRouter(prefix="/api/buses", tags=["Buses"])

def enrich_bus(bus: Bus, db: Session) -> dict:
    data = {
        "id": bus.id,
        "bus_id": bus.bus_id,
        "registration_number": bus.registration_number,
        "bus_name": bus.bus_name,
        "capacity": bus.capacity,
        "status": bus.status,
        "current_latitude": bus.current_latitude,
        "current_longitude": bus.current_longitude,
        "current_speed": bus.current_speed or 0.0,
        "last_telemetry_at": bus.last_telemetry_at,
        "created_at": bus.created_at,
        "driver_id": bus.driver_id,
        "route_id": bus.route_id,
        "driver_name": bus.driver.driver_name if bus.driver else "Unassigned",
        "route_name": bus.route.route_name if bus.route else "Unassigned",
        "route_code": bus.route.route_id if bus.route else None,
        "next_stop": "Waiting at Depot",
        "eta": "N/A",
        "delay_reason": None,
        "stop_etas": []
    }

    # Find latest active trip & delay
    active_trip = db.query(Trip).filter(
        Trip.bus_id == bus.id,
        Trip.status == "ACTIVE"
    ).order_by(Trip.id.desc()).first()

    delay_offset = 0
    if active_trip:
        data["trip_id"] = active_trip.trip_id
        latest_delay = db.query(DelayReport).filter(
            DelayReport.trip_id == active_trip.id
        ).order_by(DelayReport.id.desc()).first()
        if latest_delay:
            data["delay_reason"] = latest_delay.reason
            delay_offset = 10  # 10 min delay penalty for calculations

    # If bus has a route and coordinates, compute ETA and next stop
    if bus.route and bus.current_latitude and bus.current_longitude:
        ordered_stops = []
        for rs in bus.route.route_stops:
            if rs.stop:
                ordered_stops.append({
                    "stop_id": rs.stop.stop_id,
                    "stop_name": rs.stop.stop_name,
                    "latitude": rs.stop.latitude,
                    "longitude": rs.stop.longitude,
                    "sequence": rs.sequence,
                    "dwell_time_minutes": rs.dwell_time_minutes or 2
                })

        if ordered_stops:
            eta_info = ETAEngine.find_next_stop_and_etas(
                bus_lat=bus.current_latitude,
                bus_lon=bus.current_longitude,
                bus_speed_kmh=bus.current_speed or 25.0,
                ordered_stops=ordered_stops,
                delay_offset_minutes=delay_offset
            )
            data["next_stop"] = eta_info["next_stop"]
            data["eta"] = eta_info["eta_text"]
            data["stop_etas"] = eta_info["stop_etas"]

    return data

@router.get("", response_model=List[dict])
def get_all_buses(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Bus)
    if status:
        query = query.filter(Bus.status == status)
    buses = query.all()
    return [enrich_bus(b, db) for b in buses]

@router.get("/search")
def search_buses(
    q: str = Query("", description="Query string matching Route ID, Route name, Bus ID, Bus name, or Stop name"),
    db: Session = Depends(get_db)
):
    search_term = q.strip()
    if not search_term:
        buses = db.query(Bus).all()
        return [enrich_bus(b, db) for b in buses]

    like_term = f"%{search_term}%"

    # Search through buses matching bus_id, bus_name, route_id, route_name, or stopping at stop_name
    matching_buses = (
        db.query(Bus)
        .outerjoin(Route, Bus.route_id == Route.id)
        .outerjoin(RouteStop, Route.id == RouteStop.route_id)
        .outerjoin(Stop, RouteStop.stop_id == Stop.id)
        .filter(
            or_(
                Bus.bus_id.ilike(like_term),
                Bus.bus_name.ilike(like_term),
                Route.route_id.ilike(like_term),
                Route.route_name.ilike(like_term),
                Stop.stop_name.ilike(like_term),
            )
        )
        .distinct()
        .all()
    )

    return [enrich_bus(b, db) for b in matching_buses]

@router.get("/{id}")
def get_bus_by_id(id: int, db: Session = Depends(get_db)):
    bus = db.query(Bus).filter(Bus.id == id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    return enrich_bus(bus, db)
