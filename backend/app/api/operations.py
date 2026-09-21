import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Driver, Bus, Route, Stop, RouteStop, Trip, Telemetry, DelayReport
from app.schemas.driver import DriverCreate, DriverUpdate, DriverResponse
from app.schemas.bus import BusCreate, BusUpdate, BusResponse
from app.schemas.route import RouteCreate, RouteUpdate, RouteResponse, RouteStopCreate
from app.schemas.stop import StopCreate, StopUpdate, StopResponse
from app.auth.security import get_password_hash

router = APIRouter(prefix="/api/operations", tags=["Operations"])

# ================= DRIVER CRUD =================

@router.get("/drivers", response_model=List[DriverResponse])
def list_drivers(db: Session = Depends(get_db)):
    return db.query(Driver).order_by(Driver.id.desc()).all()

@router.post("/drivers", response_model=DriverResponse)
def create_driver(payload: DriverCreate, db: Session = Depends(get_db)):
    if db.query(Driver).filter(Driver.driver_id == payload.driver_id).first():
        raise HTTPException(status_code=400, detail="Driver ID already exists")

    driver = Driver(
        driver_id=payload.driver_id,
        driver_name=payload.driver_name,
        phone=payload.phone,
        hashed_password=get_password_hash(payload.password),
        photo=payload.photo or "/assets/default-driver.png",
        shift_start=payload.shift_start or "08:00",
        shift_end=payload.shift_end or "16:00",
        lunch_start=payload.lunch_start or "12:30",
        lunch_end=payload.lunch_end or "13:00",
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver

@router.put("/drivers/{id}", response_model=DriverResponse)
def update_driver(id: int, payload: DriverUpdate, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.id == id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    if payload.driver_name is not None:
        driver.driver_name = payload.driver_name
    if payload.phone is not None:
        driver.phone = payload.phone
    if payload.photo is not None:
        driver.photo = payload.photo
    if payload.shift_start is not None:
        driver.shift_start = payload.shift_start
    if payload.shift_end is not None:
        driver.shift_end = payload.shift_end
    if payload.lunch_start is not None:
        driver.lunch_start = payload.lunch_start
    if payload.lunch_end is not None:
        driver.lunch_end = payload.lunch_end
    if payload.password:
        driver.hashed_password = get_password_hash(payload.password)

    db.commit()
    db.refresh(driver)
    return driver

@router.delete("/drivers/{id}")
def delete_driver(id: int, db: Session = Depends(get_db)):
    driver = db.query(Driver).filter(Driver.id == id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # Safeguard: Dissociate any assigned buses so they are not orphaned
    assigned_buses = db.query(Bus).filter(Bus.driver_id == id).all()
    for b in assigned_buses:
        b.driver_id = None

    db.delete(driver)
    db.commit()
    return {"success": True, "message": f"Driver {driver.driver_id} deleted successfully"}

# ================= BUS CRUD =================

@router.get("/buses")
def list_buses(db: Session = Depends(get_db)):
    buses = db.query(Bus).order_by(Bus.id.desc()).all()
    results = []
    for b in buses:
        results.append({
            "id": b.id,
            "bus_id": b.bus_id,
            "registration_number": b.registration_number,
            "bus_name": b.bus_name,
            "capacity": b.capacity,
            "status": b.status,
            "driver_id": b.driver_id,
            "route_id": b.route_id,
            "driver_name": b.driver.driver_name if b.driver else "Unassigned",
            "route_name": b.route.route_name if b.route else "Unassigned",
            "current_latitude": b.current_latitude,
            "current_longitude": b.current_longitude,
            "current_speed": b.current_speed or 0.0,
            "created_at": b.created_at.isoformat(),
        })
    return results

@router.post("/buses")
def create_bus(payload: BusCreate, db: Session = Depends(get_db)):
    if db.query(Bus).filter(Bus.bus_id == payload.bus_id).first():
        raise HTTPException(status_code=400, detail="Bus ID already exists")

    bus = Bus(
        bus_id=payload.bus_id,
        registration_number=payload.registration_number,
        bus_name=payload.bus_name,
        capacity=payload.capacity or 50,
        driver_id=payload.driver_id,
        route_id=payload.route_id,
        status="IDLE"
    )
    db.add(bus)
    db.commit()
    db.refresh(bus)
    return {
        "success": True,
        "message": f"Bus {bus.bus_id} created successfully",
        "bus": {
            "id": bus.id,
            "bus_id": bus.bus_id,
            "bus_name": bus.bus_name,
            "registration_number": bus.registration_number,
        }
    }

@router.put("/buses/{id}")
def update_bus(id: int, payload: BusUpdate, db: Session = Depends(get_db)):
    bus = db.query(Bus).filter(Bus.id == id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    if payload.bus_name is not None:
        bus.bus_name = payload.bus_name
    if payload.registration_number is not None:
        bus.registration_number = payload.registration_number
    if payload.capacity is not None:
        bus.capacity = payload.capacity
    if payload.driver_id is not None:
        bus.driver_id = payload.driver_id if payload.driver_id > 0 else None
    if payload.route_id is not None:
        bus.route_id = payload.route_id if payload.route_id > 0 else None
    if payload.status is not None:
        bus.status = payload.status

    db.commit()
    db.refresh(bus)
    return {"success": True, "message": "Bus updated successfully"}

@router.delete("/buses/{id}")
def delete_bus(id: int, db: Session = Depends(get_db)):
    bus = db.query(Bus).filter(Bus.id == id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    # End active trips for this bus
    active_trips = db.query(Trip).filter(Trip.bus_id == id, Trip.status == "ACTIVE").all()
    for t in active_trips:
        t.status = "CANCELLED"
        t.end_time = datetime.utcnow()

    db.delete(bus)
    db.commit()
    return {"success": True, "message": f"Bus {bus.bus_id} deleted successfully"}

# ================= ROUTE & STOP CRUD =================

@router.get("/routes")
def list_routes(db: Session = Depends(get_db)):
    routes = db.query(Route).all()
    results = []
    for r in routes:
        stops_count = len(r.route_stops)
        buses_count = len(r.buses)
        results.append({
            "id": r.id,
            "route_id": r.route_id,
            "route_name": r.route_name,
            "direction": r.direction,
            "is_active": r.is_active,
            "stops_count": stops_count,
            "buses_count": buses_count,
            "stops": [
                {
                    "stop_id": rs.stop.stop_id,
                    "stop_name": rs.stop.stop_name,
                    "sequence": rs.sequence,
                    "scheduled_arrival_time": rs.scheduled_arrival_time,
                    "dwell_time_minutes": rs.dwell_time_minutes,
                    "latitude": rs.stop.latitude,
                    "longitude": rs.stop.longitude,
                }
                for rs in r.route_stops if rs.stop
            ]
        })
    return results

@router.post("/routes")
def create_route(payload: RouteCreate, db: Session = Depends(get_db)):
    if db.query(Route).filter(Route.route_id == payload.route_id).first():
        raise HTTPException(status_code=400, detail="Route ID already exists")

    route = Route(
        route_id=payload.route_id,
        route_name=payload.route_name,
        direction=payload.direction or "Outbound",
        is_active=payload.is_active if payload.is_active is not None else True
    )
    db.add(route)
    db.flush()

    # Add stops if provided
    for idx, s in enumerate(payload.stops or []):
        stop_id_val = s.stop_id or f"STP-{uuid.uuid4().hex[:6].upper()}"
        existing_stop = db.query(Stop).filter(Stop.stop_id == stop_id_val).first()
        if not existing_stop:
            existing_stop = Stop(
                stop_id=stop_id_val,
                stop_name=s.stop_name,
                latitude=s.latitude,
                longitude=s.longitude
            )
            db.add(existing_stop)
            db.flush()

        db.add(RouteStop(
            route_id=route.id,
            stop_id=existing_stop.id,
            sequence=s.sequence or (idx + 1),
            scheduled_arrival_time=s.scheduled_arrival_time or "08:00",
            dwell_time_minutes=s.dwell_time_minutes or 3
        ))

    db.commit()
    db.refresh(route)
    return {"success": True, "message": f"Route {route.route_id} created", "route_id": route.id}

@router.put("/routes/{id}")
def update_route(id: int, payload: RouteUpdate, db: Session = Depends(get_db)):
    route = db.query(Route).filter(Route.id == id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    if payload.route_name is not None:
        route.route_name = payload.route_name
    if payload.direction is not None:
        route.direction = payload.direction
    if payload.is_active is not None:
        route.is_active = payload.is_active

    db.commit()
    return {"success": True, "message": "Route updated successfully"}

@router.delete("/routes/{id}")
def delete_route(id: int, db: Session = Depends(get_db)):
    route = db.query(Route).filter(Route.id == id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    # Dissociate buses
    buses = db.query(Bus).filter(Bus.route_id == id).all()
    for b in buses:
        b.route_id = None

    db.delete(route)
    db.commit()
    return {"success": True, "message": f"Route {route.route_id} deleted"}

@router.post("/routes/{id}/stops")
def add_stop_to_route(id: int, payload: RouteStopCreate, db: Session = Depends(get_db)):
    route = db.query(Route).filter(Route.id == id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    stop_id_val = payload.stop_id or f"STP-{uuid.uuid4().hex[:6].upper()}"
    stop = db.query(Stop).filter(Stop.stop_id == stop_id_val).first()
    if not stop:
        stop = Stop(
            stop_id=stop_id_val,
            stop_name=payload.stop_name,
            latitude=payload.latitude,
            longitude=payload.longitude
        )
        db.add(stop)
        db.flush()

    new_rs = RouteStop(
        route_id=route.id,
        stop_id=stop.id,
        sequence=payload.sequence,
        scheduled_arrival_time=payload.scheduled_arrival_time or "08:00",
        dwell_time_minutes=payload.dwell_time_minutes or 3
    )
    db.add(new_rs)
    db.commit()
    return {"success": True, "message": f"Stop {stop.stop_name} added to route {route.route_id}"}

@router.put("/stops/{id}")
def update_stop(id: int, payload: StopUpdate, db: Session = Depends(get_db)):
    stop = db.query(Stop).filter(Stop.id == id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    if payload.stop_name is not None:
        stop.stop_name = payload.stop_name
    if payload.latitude is not None:
        stop.latitude = payload.latitude
    if payload.longitude is not None:
        stop.longitude = payload.longitude

    db.commit()
    return {"success": True, "message": "Stop updated successfully"}

@router.delete("/stops/{id}")
def delete_stop(id: int, db: Session = Depends(get_db)):
    stop = db.query(Stop).filter(Stop.id == id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    db.delete(stop)
    db.commit()
    return {"success": True, "message": "Stop deleted successfully"}

# ================= TRIPS & TELEMETRY MONITOR =================

@router.get("/trips")
def list_trips(db: Session = Depends(get_db)):
    trips = db.query(Trip).order_by(Trip.id.desc()).limit(50).all()
    results = []
    for t in trips:
        delays = [d.reason for d in t.delays]
        results.append({
            "id": t.id,
            "trip_id": t.trip_id,
            "bus_id": t.bus.bus_id if t.bus else "N/A",
            "bus_name": t.bus.bus_name if t.bus else "N/A",
            "route_id": t.route.route_id if t.route else "N/A",
            "route_name": t.route.route_name if t.route else "N/A",
            "driver_name": t.driver.driver_name if t.driver else "N/A",
            "start_time": t.start_time.strftime("%Y-%m-%d %H:%M:%S") if t.start_time else "",
            "end_time": t.end_time.strftime("%Y-%m-%d %H:%M:%S") if t.end_time else None,
            "status": t.status,
            "delays": delays,
        })
    return results

@router.get("/telemetry")
def list_telemetry_logs(db: Session = Depends(get_db)):
    telemetry_records = db.query(Telemetry).order_by(Telemetry.id.desc()).limit(100).all()
    return [
        {
            "id": tr.id,
            "trip_id": tr.trip.trip_id if tr.trip else str(tr.trip_id),
            "bus_id": tr.bus.bus_id if tr.bus else str(tr.bus_id),
            "latitude": tr.latitude,
            "longitude": tr.longitude,
            "speed": tr.speed,
            "accuracy": tr.accuracy,
            "source": tr.source,
            "timestamp": tr.timestamp.strftime("%H:%M:%S"),
        }
        for tr in telemetry_records
    ]
