import logging
from sqlalchemy.orm import Session
from app.models import (
    Passenger, Driver, Route, Stop, RouteStop, Bus, TravelUpdate
)
from app.auth.security import get_password_hash

logger = logging.getLogger("transitnow.seed")

def seed_database(db: Session):
    """
    Populates initial realistic transit network data for Madurai TransitNow.
    """
    # Check if data is already seeded
    if db.query(Route).count() > 0:
        logger.info("Database already seeded. Skipping initial data injection.")
        return

    logger.info("Seeding database with Madurai public transportation data...")

    # 1. Create Default Passenger for quick testing
    test_passenger = Passenger(
        full_name="Anand Kumar",
        phone="9840123456",
        email="passenger@transitnow.com",
        hashed_password=get_password_hash("password123")
    )
    db.add(test_passenger)

    # 2. Create Drivers
    driver1 = Driver(
        driver_id="DRV001",
        driver_name="K. Murugan",
        phone="9876543210",
        hashed_password=get_password_hash("password123"),
        photo="/assets/driver1.png",
        shift_start="08:00",
        shift_end="16:00",
        lunch_start="12:30",
        lunch_end="13:00"
    )
    driver2 = Driver(
        driver_id="DRV002",
        driver_name="S. Arumugam",
        phone="9876543211",
        hashed_password=get_password_hash("password123"),
        photo="/assets/driver2.png",
        shift_start="14:00",
        shift_end="22:00",
        lunch_start="18:00",
        lunch_end="18:30"
    )
    db.add_all([driver1, driver2])
    db.flush()

    # 3. Create Stops
    stops_data = [
        {"stop_id": "STP001", "stop_name": "Madurai Central", "latitude": 9.9195, "longitude": 78.1118},
        {"stop_id": "STP002", "stop_name": "Thirumalai Nayakkar Mahal", "latitude": 9.9152, "longitude": 78.1235},
        {"stop_id": "STP003", "stop_name": "Goripalayam", "latitude": 9.9325, "longitude": 78.1285},
        {"stop_id": "STP004", "stop_name": "Mattuthavani", "latitude": 9.9482, "longitude": 78.1585},
        {"stop_id": "STP005", "stop_name": "Periyar Bus Stand", "latitude": 9.9175, "longitude": 78.1130},
        {"stop_id": "STP006", "stop_name": "Simmakkal", "latitude": 9.9270, "longitude": 78.1210},
        {"stop_id": "STP007", "stop_name": "Othakadai", "latitude": 9.9700, "longitude": 78.1900},
        {"stop_id": "STP008", "stop_name": "Thirunagar", "latitude": 9.8750, "longitude": 78.0750},
        {"stop_id": "STP009", "stop_name": "Pasumalai", "latitude": 9.8950, "longitude": 78.0850},
        {"stop_id": "STP010", "stop_name": "Palanganatham", "latitude": 9.9050, "longitude": 78.1000},
    ]
    created_stops = {}
    for s_dict in stops_data:
        stop = Stop(**s_dict)
        db.add(stop)
        db.flush()
        created_stops[stop.stop_id] = stop

    # 4. Create Routes
    # Route 21G: Madurai Central -> Thirumalai Nayakkar Mahal -> Goripalayam -> Mattuthavani
    route_21g = Route(
        route_id="21G",
        route_name="Madurai Central - Mattuthavani",
        direction="Outbound",
        is_active=True
    )
    # Route 10A: Periyar -> Madurai Central -> Simmakkal -> Othakadai
    route_10a = Route(
        route_id="10A",
        route_name="Periyar - Othakadai Express",
        direction="Outbound",
        is_active=True
    )
    # Route 48P: Thirunagar -> Pasumalai -> Palanganatham -> Periyar
    route_48p = Route(
        route_id="48P",
        route_name="Thirunagar - Periyar Bus Stand",
        direction="Outbound",
        is_active=True
    )
    db.add_all([route_21g, route_10a, route_48p])
    db.flush()

    # 5. Route Stops Sequence for 21G
    r21g_stops = [
        {"stop_id": "STP001", "sequence": 1, "scheduled_arrival_time": "08:30", "dwell_time_minutes": 5},
        {"stop_id": "STP002", "sequence": 2, "scheduled_arrival_time": "08:40", "dwell_time_minutes": 3},
        {"stop_id": "STP003", "sequence": 3, "scheduled_arrival_time": "08:50", "dwell_time_minutes": 4},
        {"stop_id": "STP004", "sequence": 4, "scheduled_arrival_time": "09:05", "dwell_time_minutes": 5},
    ]
    for rs in r21g_stops:
        db.add(RouteStop(
            route_id=route_21g.id,
            stop_id=created_stops[rs["stop_id"]].id,
            sequence=rs["sequence"],
            scheduled_arrival_time=rs["scheduled_arrival_time"],
            dwell_time_minutes=rs["dwell_time_minutes"],
        ))

    # Route Stops Sequence for 10A
    r10a_stops = [
        {"stop_id": "STP005", "sequence": 1, "scheduled_arrival_time": "09:00", "dwell_time_minutes": 5},
        {"stop_id": "STP001", "sequence": 2, "scheduled_arrival_time": "09:10", "dwell_time_minutes": 4},
        {"stop_id": "STP006", "sequence": 3, "scheduled_arrival_time": "09:25", "dwell_time_minutes": 3},
        {"stop_id": "STP007", "sequence": 4, "scheduled_arrival_time": "09:50", "dwell_time_minutes": 5},
    ]
    for rs in r10a_stops:
        db.add(RouteStop(
            route_id=route_10a.id,
            stop_id=created_stops[rs["stop_id"]].id,
            sequence=rs["sequence"],
            scheduled_arrival_time=rs["scheduled_arrival_time"],
            dwell_time_minutes=rs["dwell_time_minutes"],
        ))

    # 6. Create Buses and Assign Drivers & Routes
    bus1 = Bus(
        bus_id="BUS001",
        registration_number="TN-58-AA-1234",
        bus_name="Madurai City Express 21G",
        capacity=52,
        driver_id=driver1.id,
        route_id=route_21g.id,
        status="ACTIVE",
        current_latitude=9.9195,
        current_longitude=78.1118,
        current_speed=0.0
    )
    bus2 = Bus(
        bus_id="BUS002",
        registration_number="TN-58-AB-5678",
        bus_name="Vaigai Metro Liner 10A",
        capacity=50,
        driver_id=driver2.id,
        route_id=route_10a.id,
        status="ACTIVE",
        current_latitude=9.9175,
        current_longitude=78.1130,
        current_speed=0.0
    )
    db.add_all([bus1, bus2])

    # 7. Travel Updates
    updates = [
        TravelUpdate(
            title="Chithirai Festival Transit Advisory",
            category="Festival advisory",
            summary="Special frequency buses deployed every 5 mins along Goripalayam and Mattuthavani corridors.",
            severity="info"
        ),
        TravelUpdate(
            title="Periyar Bus Stand Bay Maintenance",
            category="Route diversion",
            summary="Bay 4 temporary resurfacing underway; departures rerouted to Platform Bay 6.",
            severity="warning"
        ),
        TravelUpdate(
            title="Late Night Vaigai Line Extended",
            category="Service timing update",
            summary="Hourly night buses operating from Mattuthavani Integrated Terminal through 01:00 AM.",
            severity="info"
        )
    ]
    db.add_all(updates)

    db.commit()
    logger.info("Database seeding completed successfully.")
