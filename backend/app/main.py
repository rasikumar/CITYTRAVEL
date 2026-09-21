import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.data_seed import seed_database
from app.websocket import manager
from app.api import (
    auth_router,
    passenger_router,
    routes_router,
    buses_router,
    stops_router,
    driver_router,
    operations_router,
    tickets_router,
    chat_router,
    travel_updates_router,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("transitnow")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing TransitNow database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed realistic Madurai transit data on startup
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    logger.info("TransitNow backend started successfully.")
    yield
    logger.info("TransitNow backend shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    description="Real-Time Bus Location, ETA, Route, Ticketing & Transit Information Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for decoupled frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register REST API Routers
app.include_router(auth_router)
app.include_router(passenger_router)
app.include_router(routes_router)
app.include_router(buses_router)
app.include_router(stops_router)
app.include_router(driver_router)
app.include_router(operations_router)
app.include_router(tickets_router)
app.include_router(chat_router)
app.include_router(travel_updates_router)

# Real-time WebSocket Endpoint
@app.websocket("/ws/transit")
async def websocket_transit_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep receiving incoming messages or ping/pong heartbeats
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket client closed with exception: {e}")
        manager.disconnect(websocket)

# Determine Paths for the 3 Decoupled Applications
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PASSENGER_DIR = os.path.join(BASE_DIR, "passenger-app")
DRIVER_DIR = os.path.join(BASE_DIR, "driver-app")
OPERATIONS_DIR = os.path.join(BASE_DIR, "operations-app")

# Ensure directories exist
os.makedirs(PASSENGER_DIR, exist_ok=True)
os.makedirs(DRIVER_DIR, exist_ok=True)
os.makedirs(OPERATIONS_DIR, exist_ok=True)

# Mount Clean URL routes for Frontends
@app.get("/")
def root():
    return RedirectResponse(url="/passenger")

# 1. Passenger Application Routes
@app.get("/passenger")
def passenger_home():
    return FileResponse(os.path.join(PASSENGER_DIR, "index.html"))

@app.get("/passenger/login")
def passenger_login():
    return FileResponse(os.path.join(PASSENGER_DIR, "login.html"))

@app.get("/passenger/register")
def passenger_register():
    return FileResponse(os.path.join(PASSENGER_DIR, "register.html"))

@app.get("/passenger/profile")
def passenger_profile():
    return FileResponse(os.path.join(PASSENGER_DIR, "profile.html"))

@app.get("/passenger/tickets")
def passenger_tickets():
    return FileResponse(os.path.join(PASSENGER_DIR, "tickets.html"))

app.mount("/passenger", StaticFiles(directory=PASSENGER_DIR, html=True), name="passenger-app")

# 2. Driver Application Routes
@app.get("/driver-app")
def driver_dashboard():
    return FileResponse(os.path.join(DRIVER_DIR, "dashboard.html"))

@app.get("/driver-app/login")
def driver_login():
    return FileResponse(os.path.join(DRIVER_DIR, "login.html"))

@app.get("/driver-app/trip")
def driver_trip():
    return FileResponse(os.path.join(DRIVER_DIR, "trip.html"))

@app.get("/driver-app/profile")
def driver_profile():
    return FileResponse(os.path.join(DRIVER_DIR, "profile.html"))

app.mount("/driver-app", StaticFiles(directory=DRIVER_DIR, html=True), name="driver-app")

# 3. Operations Application Routes
@app.get("/operations")
def operations_dashboard():
    return FileResponse(os.path.join(OPERATIONS_DIR, "index.html"))

@app.get("/operations/routes")
def operations_routes():
    return FileResponse(os.path.join(OPERATIONS_DIR, "routes.html"))

@app.get("/operations/route-create")
def operations_route_create():
    return FileResponse(os.path.join(OPERATIONS_DIR, "route-create.html"))

@app.get("/operations/route-edit")
def operations_route_edit():
    return FileResponse(os.path.join(OPERATIONS_DIR, "route-edit.html"))

@app.get("/operations/buses")
def operations_buses():
    return FileResponse(os.path.join(OPERATIONS_DIR, "buses.html"))

@app.get("/operations/drivers")
def operations_drivers():
    return FileResponse(os.path.join(OPERATIONS_DIR, "drivers.html"))

@app.get("/operations/trips")
def operations_trips():
    return FileResponse(os.path.join(OPERATIONS_DIR, "trips.html"))

app.mount("/operations", StaticFiles(directory=OPERATIONS_DIR, html=True), name="operations-app")
