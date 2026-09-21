import json
import logging
from typing import List, Dict, Any, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("transitnow.websocket")

class ConnectionManager:
    """
    Manages active WebSocket connections for real-time transit telemetry streaming.
    Supports broad broadcasting to passengers, drivers, and operations observers.
    """
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"New client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"Client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast_json(self, data: Dict[str, Any]):
        """
        Broadcast JSON payload to all active clients safely, pruning broken connections.
        """
        if not self.active_connections:
            return

        dead_connections = set()
        for connection in list(self.active_connections):
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.warning(f"Error broadcasting to client: {e}")
                dead_connections.add(connection)

        for dead in dead_connections:
            self.active_connections.discard(dead)

    async def broadcast_telemetry(
        self,
        bus_id: str,
        route_id: str,
        trip_id: str,
        latitude: float,
        longitude: float,
        speed: float,
        accuracy: float,
        next_stop: str = None,
        eta: str = None,
        trip_status: str = "ACTIVE",
        delay_reason: str = None,
        telemetry_source: str = "phone_gps",
        timestamp: str = None
    ):
        payload = {
            "type": "telemetry",
            "bus_id": bus_id,
            "route_id": route_id,
            "trip_id": trip_id,
            "latitude": latitude,
            "longitude": longitude,
            "speed": speed,
            "accuracy": accuracy,
            "next_stop": next_stop,
            "eta": eta,
            "trip_status": trip_status,
            "delay_reason": delay_reason,
            "telemetry_source": telemetry_source,
            "timestamp": timestamp,
        }
        await self.broadcast_json(payload)

    async def broadcast_delay(self, bus_id: str, trip_id: str, reason: str, note: str = None):
        payload = {
            "type": "delay",
            "bus_id": bus_id,
            "trip_id": trip_id,
            "reason": reason,
            "note": note,
        }
        await self.broadcast_json(payload)

    async def broadcast_trip_ended(self, bus_id: str, trip_id: str):
        payload = {
            "type": "trip_ended",
            "bus_id": bus_id,
            "trip_id": trip_id,
            "trip_status": "ENDED",
        }
        await self.broadcast_json(payload)

manager = ConnectionManager()
