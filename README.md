# TRANSITNOW
### Real-Time Bus Location, ETA, Route, Ticketing & Transit Information Platform

TRANSITNOW is a production-grade, real-time public transportation platform featuring live vehicle tracking, continuous GPS telemetry streaming, Kalman filter trajectory smoothing, ML-based ETA predictions, route & stop management with OpenStreetMap Nominatim geocoding, contactless digital ticketing with mock payment gateways, and an AI transit assistant.

---

## 🏛️ Architecture: Three Decoupled Frontend Applications

This project strictly adheres to the architectural requirement of having **three completely separate frontend applications** with dedicated source directories, separate pages, separate navigation, separate assets, and separate JavaScript ES modules:

```text
                         ┌──────────────────────┐
                         │   FASTAPI BACKEND     │
                         │                      │
                         │ REST API + WebSocket │
                         └──────────┬───────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             │                      │                      │
             ▼                      ▼                      ▼

     PASSENGER APP            DRIVER APP             OPERATIONS APP
       separate                 separate                separate
       frontend                 frontend                frontend
   (/passenger)             (/driver-app)           (/operations)
```

1. **Passenger Application** (`passenger-app/` at `/passenger`):
   - Passenger-only interface (no driver or operations navigation).
   - Unified search (Route ID, Route name, Bus ID, Bus name, Stop name).
   - Medium-size Leaflet map with 3 tile layers (Map, Satellite, Dark) and Recenter control.
   - Visually distinct markers: 👤 Passenger location and 🚌 Bus marker displaying live Bus ID.
   - Live marker popup: Speed, Distance from passenger (Haversine), Next stop, ETA, Trip status, Delay reason.
   - Browser geolocation ("Use my location" calculating live distance).
   - Real-time WebSocket connection to `/ws/transit` (smooth marker updates without full map re-creation or page reload).
   - Stop arrival proximity notifications ("Approaching stop" / "Reached stop").
   - Travel updates & advisory cards.
   - Floating AI Transit Assistant calling backend transit functions without hallucinating.
   - Digital ticketing with QR pass generation and simulated UPI payments (Google Pay, PhonePe, Paytm, RuPay).
   - Complete Light and Dark theme support across all components.

2. **Driver Application** (`driver-app/` at `/driver-app`):
   - Driver-only cockpit interface (no passenger or operations navigation).
   - Driver authentication with Driver ID and hashed password.
   - Dashboard displaying **only** the driver's assigned bus and route with duty shift and lunch schedule.
   - Big **START TRIP** button that validates assignments and requests browser GPS.
   - High-contrast cockpit telemetry gauges: GPS Status, Accuracy, Speed, Latitude, Longitude, Active Trip, Next Stop, ETA.
   - Sends immediate first GPS coordinate upon start, then streams updates to `POST /api/driver/telemetry`.
   - Standardized delay reporting modal (`Traffic issue`, `Accident`, `Road closure`, `Passenger boarding`, `Vehicle issue`, `Weather`, `Operational delay`, `Other`) broadcast live to passengers.
   - **END TRIP** button marking trip `ENDED` and notifying passengers.
   - **Route Playback Simulator** fallback mode for environments without hardware GPS (clearly labeled `ROUTE PLAYBACK`, moving Stop 1 ➔ 2 ➔ 3 ➔ 4 ➔ 10-minute wait ➔ 3 ➔ 2 ➔ 1).

3. **Operations / Admin Application** (`operations-app/` at `/operations`):
   - Operations-only fleet management portal (compact, high-density layout).
   - Real-time KPI counters (Routes, Buses, Drivers, Active Trips, Delays).
   - **Driver Management**: Register drivers, configure shifts & lunch breaks, update and safely delete (preventing orphaned bus assignments).
   - **Bus Management**: Register buses, assign driver & route, edit capacity and status, delete with active-trip safeguards.
   - **Route & Stop Management**:
     - Create and edit routes.
     - Single location input search powered by OpenStreetMap Nominatim auto-populating latitude and longitude coordinates (with manual overrides allowed).
     - Configure scheduled arrival times, dwell time limits, and stop sequences.
     - Add, delete, and reorder stops.
   - **Live Monitor**: Audit active trips and inspect incoming GPS telemetry logs.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.12+, FastAPI, Uvicorn, SQLAlchemy, Pydantic, WebSockets, Alembic.
- **Database**: PostgreSQL with PostGIS (via Docker) or automatic SQLite fallback for zero-dependency local runs.
- **Cache & PubSub**: Redis with in-memory WebSocket broadcast fallback.
- **Machine Learning & GIS**: Scikit-learn (`RandomForestRegressor`), NumPy, Pandas, Joblib, Kalman filter (1D/2D position and velocity smoothing with teleportation jump rejection), Haversine spherical distance.
- **Frontends**: HTML5, CSS3, JavaScript ES modules (Vanilla, zero heavy framework overhead).
- **Mapping**: Leaflet, OpenStreetMap, Esri World Imagery, Carto Dark, OpenStreetMap Nominatim geocoding.

---

## 📁 Project Directory Structure

```text
transitnow/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, static mounts, routers, CORS, startup seed
│   │   ├── config.py                # Configuration and environment settings
│   │   ├── database.py              # SQLAlchemy engine and sessionmaker
│   │   ├── websocket.py             # WebSocket ConnectionManager (/ws/transit)
│   │   ├── data_seed.py             # Seed dataset (Route 21G, 10A, 48P, buses, drivers, alerts)
│   │   ├── models/                  # Database models (Passenger, Driver, Bus, Route, Stop, etc.)
│   │   ├── schemas/                 # Pydantic validation schemas
│   │   ├── api/                     # REST API Routers (auth, passenger, routes, buses, driver, ops, etc.)
│   │   ├── services/                # Business logic (Kalman, Haversine, ETA, Mock Payment Provider)
│   │   └── auth/                    # Password hashing and JWT security
│   ├── migrations/                  # Alembic database migration environment
│   ├── tests/                       # Automated pytest test suite
│   ├── requirements.txt
│   └── .env.example
├── passenger-app/                   # Separate Frontend 1: Passenger Only
│   ├── index.html                   # Live map, search, live buses, advisories, AI assistant
│   ├── login.html                   # Sign in with real link to register
│   ├── register.html                # Passenger registration with auto-login redirect
│   ├── profile.html                 # Profile view
│   ├── tickets.html                 # Digital ticketing with QR pass
│   ├── css/style.css                # Mobile-first stylesheet with light & dark theme tokens
│   └── js/                          # Modular ES scripts (map, websocket, api, auth, tickets, ai)
├── driver-app/                      # Separate Frontend 2: Driver Only
│   ├── login.html                   # Driver sign in (Driver ID + password)
│   ├── dashboard.html               # Assigned bus, route, shift, and START TRIP
│   ├── trip.html                    # Active cockpit: GPS telemetry, delay modal, End Trip, playback
│   ├── profile.html                 # Driver profile
│   ├── css/driver.css               # High-contrast cockpit stylesheet
│   └── js/                          # Modular ES scripts (gps tracker, playback, trip controller)
├── operations-app/                  # Separate Frontend 3: Operations Only
│   ├── index.html                   # KPI dashboard and active trip monitor
│   ├── routes.html                  # Routes list
│   ├── route-create.html            # Route builder with OSM Nominatim geocoding
│   ├── route-edit.html              # Route editor (reorder, arrival/dwell times, add/delete stops)
│   ├── buses.html                   # Bus fleet management & driver/route assignment
│   ├── drivers.html                 # Driver roster management
│   ├── trips.html                   # Live trips monitor & telemetry audit log
│   ├── css/operations.css           # Operations stylesheet
│   └── js/                          # Modular ES scripts (nominatim, routes, buses, drivers, trips)
├── ml/
│   ├── kalman.py                    # Standalone 2D Kalman filter
│   ├── eta_model.py                 # Scikit-learn ETA prediction model wrapper
│   └── train_model.py               # Synthetic transit feature training pipeline
├── data/
│   └── seed/
│       └── seed_madurai.json        # Madurai public transportation network seed
├── docker-compose.yml               # Multi-container orchestration (FastAPI + PostGIS + Redis)
├── Dockerfile                       # Python 3.12 container specification
└── README.md
```

---

## 🚀 Quickstart & Run Commands

### 1. Local Run (Zero Configuration, Auto SQLite Fallback)

Open your terminal in the project root:

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate

# Linux / macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI backend with live reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

*Upon startup, the database tables and realistic seed data for the Madurai Transit Network are automatically initialized.*

### 2. Docker Run (PostgreSQL + PostGIS + Redis)

```bash
docker-compose up --build
```

---

## 🌐 Application URLs

Once running, access each separate application:

| Application | URL | Description |
| :--- | :--- | :--- |
| **Passenger Application** | [http://localhost:8000/passenger](http://localhost:8000/passenger) | Live bus tracking, search, map, ETAs, tickets, AI chat |
| **Driver Application** | [http://localhost:8000/driver-app](http://localhost:8000/driver-app) | Driver cockpit, START TRIP, GPS telemetry, delay reporting |
| **Operations Application** | [http://localhost:8000/operations](http://localhost:8000/operations) | Fleet control, routes, OSM Nominatim geocoding, buses, drivers |
| **Interactive API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Swagger UI for all REST endpoints |

---

## 🧪 Pre-Configured Test Credentials

### Passenger
- **Email / Phone**: `passenger@transitnow.com` or `9840123456`
- **Password**: `password123`
- *(Or create any new account via [Create Passenger Account](http://localhost:8000/passenger/register))*

### Drivers
- **Driver 1 ID**: `DRV001` | **Password**: `password123` *(Assigned to BUS001 on Route 21G)*
- **Driver 2 ID**: `DRV002` | **Password**: `password123` *(Assigned to BUS002 on Route 10A)*

---

## 🔄 Live End-to-End Test: Driver to Passenger Connection

To verify real-time GPS streaming:

1. Open **Window 1**: Navigate to [http://localhost:8000/passenger](http://localhost:8000/passenger). Observe the map centered on Madurai with bus markers.
2. Open **Window 2**: Navigate to [http://localhost:8000/driver-app/login](http://localhost:8000/driver-app/login).
3. Log in with Driver ID `DRV001` and password `password123`.
4. On the Driver Dashboard, observe that only your assigned bus (`BUS001`) and route (`Route 21G`) appear.
5. Click **START TRIP**. Allow browser GPS location (or click **ROUTE PLAYBACK** if running on a desktop machine without GPS movement).
6. In **Window 1 (Passenger)**: Observe that `BUS001` smoothly moves in real time across the Leaflet map without page reloads or full map recreations!
7. In **Window 2 (Driver)**: Click **Report Route Delay** and select `Traffic issue`. Observe that in Window 1 the bus card and popup immediately flag the delay!

---

## 🚦 Automated Test Suite

Run the comprehensive pytest test suite covering authentication, telemetry, Kalman filtering, operations CRUD, ticketing, and AI assistant tool calls:

```bash
cd backend
pytest tests/ -v
```
