from app.api.auth import router as auth_router
from app.api.passenger import router as passenger_router
from app.api.routes import router as routes_router
from app.api.buses import router as buses_router
from app.api.stops import router as stops_router
from app.api.driver import router as driver_router
from app.api.operations import router as operations_router
from app.api.tickets import router as tickets_router
from app.api.chat import router as chat_router
from app.api.travel_updates import router as travel_updates_router

__all__ = [
    "auth_router",
    "passenger_router",
    "routes_router",
    "buses_router",
    "stops_router",
    "driver_router",
    "operations_router",
    "tickets_router",
    "chat_router",
    "travel_updates_router",
]
