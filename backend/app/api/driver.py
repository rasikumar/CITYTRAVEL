import time
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Driver, Bus, Route, Trip, Telemetry, DelayReport
from app.schemas.driver import DriverProfileResponse
from app.schemas.trip import TripStart, TripEnd
from app.schemas.telemetry import TelemetryIngest
from app.schemas.delay import DelayCreate
from app.auth.security import decode_access_token
from app.services.kalman import get_bus_kalman_filter
from app.services.eta import ETAEngine
from app.websocket import manager

router = APIRouter(prefix="/api/driver", tags=["Driver"])

def get_current_driver(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Driver:
    if not authorization or not authorization.startswith("Bearer "):
        # Fallback to driver DRV001 for easy development testing
        driver = db.query(Driver).filter(Driver.driver_id == "DRV001").first()
        if driver:
            return driver
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Driver token required"
        )

    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload or payload.get("role") != "driver":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired driver credentials"
        )

    driver_id_pk = payload.get("sub")
    driver = db.query(Driver).filter(Driver.id == int(driver_id_pk)).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver record not found")
    return driver

@router.get("/profile")
def get_driver_profile(
    driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    # Driver can only see THEIR assigned bus
    assigned_bus = db.query(Bus).filter(Bus.driver_id == driver.id).first()
    
    assigned_route = None
    if assigned_bus and assigned_bus.route:
        route = assigned_bus.route
        assigned_route = {
            "id": route.id,
            "route_id": route.route_id,
            "route_name": route.route_name,
            "direction": route.direction,
            "stops": [
                {
                    "stop_id": rs.stop.stop_id,
                    "stop_name": rs.stop.stop_name,
                    "latitude": rs.stop.latitude,
                    "longitude": rs.stop.longitude,
                    "sequence": rs.sequence,
                    "scheduled_arrival_time": rs.scheduled_arrival_time,
                    "dwell_time_minutes": rs.dwell_time_minutes or 2,
                }
                for rs in route.route_stops if rs.stop
            ]
        }

    # Active trip if any
    active_trip = None
    if assigned_bus:
        trip = db.query(Trip).filter(
            Trip.bus_id == assigned_bus.id,
            Trip.status == "ACTIVE"
        ).order_by(Trip.id.desc()).first()
        if trip:
            active_trip = {
                "id": trip.id,
                "trip_id": trip.trip_id,
                "start_time": trip.start_time.isoformat(),
                "status": trip.status,
            }

    return {
        "driver": {
            "id": driver.id,
            "driver_id": driver.driver_id,
            "driver_name": driver.driver_name,
            "phone": driver.phone,
            "photo": driver.photo,
            "shift_start": driver.shift_start,
            "shift_end": driver.shift_end,
            "lunch_start": driver.lunch_start,
            "lunch_end": driver.lunch_end,
        },
        "assigned_bus": {
            "id": assigned_bus.id,
            "bus_id": assigned_bus.bus_id,
            "registration_number": assigned_bus.registration_number,
            "bus_name": assigned_bus.bus_name,
            "capacity": assigned_bus.capacity,
            "status": assigned_bus.status,
        } if assigned_bus else None,
        "assigned_route": assigned_route,
        "active_trip": active_trip,
    }

@router.post("/trips/start")
async def start_trip(
    payload: TripStart,
    driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    # Validate assigned bus
    bus = db.query(Bus).filter(Bus.bus_id == payload.bus_id, Bus.driver_id == driver.id).first()
    if not bus:
        raise HTTPException(status_code=400, detail="Bus is not assigned to this driver")

    # Validate route
    route = db.query(Route).filter(Route.route_id == payload.route_id).first()
    if not route:
        raise HTTPException(status_code=400, detail="Specified route does not exist")

    # End any existing active trips for this bus
    existing_trips = db.query(Trip).filter(Trip.bus_id == bus.id, Trip.status == "ACTIVE").all()
    for et in existing_trips:
        et.status = "ENDED"
        et.end_time = datetime.utcnow()

    trip_id_str = f"TRIP-{datetime.utcnow().strftime('%Y%m%d%H%M')}-{uuid.uuid4().hex[:4].upper()}"
    new_trip = Trip(
        trip_id=trip_id_str,
        bus_id=bus.id,
        driver_id=driver.id,
        route_id=route.id,
        start_time=datetime.utcnow(),
        status="ACTIVE"
    )
    bus.status = "ACTIVE"
    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)

    return {
        "success": True,
        "trip_id": new_trip.trip_id,
        "bus_id": bus.bus_id,
        "route_id": route.route_id,
        "status": "ACTIVE",
        "message": f"Trip {new_trip.trip_id} successfully started"
    }

@router.post("/trips/end")
async def end_trip(
    payload: TripEnd,
    driver: Driver = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    trip = db.query(Trip).filter(Trip.trip_id == payload.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip.status = "ENDED"
    trip.end_time = datetime.utcnow()
    
    bus = db.query(Bus).filter(Bus.id == trip.bus_id).first()
    if bus:
        bus.status = "IDLE"
        bus.current_speed = 0.0

    db.commit()

    # Broadcast trip ended through WebSocket so passenger UI clears active marker/status
    if bus:
        await manager.broadcast_trip_ended(bus_id=bus.bus_id, trip_id=trip.trip_id)

    return {
        "success": True,
        "trip_id": trip.trip_id,
        "status": "ENDED",
        "message": "Trip ended successfully. Passenger view updated."
    }

@router.post("/telemetry")
async def ingest_telemetry(
    payload: TelemetryIngest,
    db: Session = Depends(get_db)
):
    bus = db.query(Bus).filter(Bus.bus_id == payload.bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    trip = db.query(Trip).filter(Trip.trip_id == payload.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Active trip not found")

    # 1. Kalman Filter & Jump Rejection Pipeline
    kalman = get_bus_kalman_filter(bus.bus_id)
    f_lat, f_lon, f_speed, is_valid = kalman.validate_and_filter(
        lat=payload.latitude,
        lon=payload.longitude,
        speed=payload.speed or 0.0,
        timestamp=time.time()
    )

    if not is_valid:
        # Rejected anomaly/impossible jump
        return {
            "status": "rejected_jump",
            "message": "Telemetry rejected due to impossible distance or velocity delta",
            "retained_latitude": f_lat,
            "retained_longitude": f_lon
        }

    # 2. Update Bus in Database
    now = datetime.utcnow()
    bus.current_latitude = f_lat
    bus.current_longitude = f_lon
    bus.current_speed = f_speed
    bus.last_telemetry_at = now

    # 3. Store Telemetry Record
    telemetry_entry = Telemetry(
        trip_id=trip.id,
        bus_id=bus.id,
        driver_id=trip.driver_id,
        route_id=trip.route_id,
        latitude=f_lat,
        longitude=f_lon,
        speed=f_speed,
        accuracy=payload.accuracy or 10.0,
        source=payload.source or "phone_gps",
        timestamp=now
    )
    db.add(telemetry_entry)
    db.commit()

    # 4. Compute Next Stop & ETA dynamically
    next_stop = "Depot"
    eta = "N/A"
    if bus.route:
        ordered_stops = [
            {
                "stop_id": rs.stop.stop_id,
                "stop_name": rs.stop.stop_name,
                "latitude": rs.stop.latitude,
                "longitude": rs.stop.longitude,
                "sequence": rs.sequence,
                "dwell_time_minutes": rs.dwell_time_minutes or 2
            }
            for rs in bus.route.route_stops if rs.stop
        ]
        if ordered_stops:
            eta_info = ETAEngine.find_next_stop_and_etas(
                bus_lat=f_lat,
                bus_lon=f_lon,
                bus_speed_kmh=f_speed,
                ordered_stops=ordered_stops
            )
            next_stop = eta_info["next_stop"]
            eta = eta_info["eta_text"]

    # 5. Broadcast to WebSocket for Passenger App
    await manager.broadcast_telemetry(
        bus_id=bus.bus_id,
        route_id=payload.route_id,
        trip_id=trip.trip_id,
        latitude=f_lat,
        longitude=f_lon,
        speed=f_speed,
        accuracy=payload.accuracy or 10.0,
        next_stop=next_stop,
        eta=eta,
        trip_status="ACTIVE",
        telemetry_source=payload.source or "phone_gps",
        timestamp=now.isoformat()
    )

    return {
        "status": "success",
        "bus_id": bus.bus_id,
        "filtered_latitude": f_lat,
        "filtered_longitude": f_lon,
        "filtered_speed": f_speed,
        "next_stop": next_stop,
        "eta": eta
    }

@router.post("/delay")
async def report_delay(
    payload: DelayCreate,
    db: Session = Depends(get_db)
):
    bus = db.query(Bus).filter(Bus.bus_id == payload.bus_id).first()
    trip = db.query(Trip).filter(Trip.trip_id == payload.trip_id).first()
    driver = db.query(Driver).filter(Driver.driver_id == payload.driver_id).first()

    if not bus or not trip or not driver:
        raise HTTPException(status_code=404, detail="Entity not found for delay report")

    delay_report = DelayReport(
        trip_id=trip.id,
        bus_id=bus.id,
        driver_id=driver.id,
        reason=payload.reason,
        note=payload.note,
        reported_at=datetime.utcnow()
    )
    db.add(delay_report)
    db.commit()

    # Broadcast delay reason over WebSocket to passenger app
    await manager.broadcast_delay(
        bus_id=bus.bus_id,
        trip_id=trip.trip_id,
        reason=payload.reason,
        note=payload.note
    )

    return {
        "status": "success",
        "message": f"Delay '{payload.reason}' reported and broadcast to passengers."
    }
