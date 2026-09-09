import json
import uuid
from typing import Dict, List, Set, Any
from fastapi import WebSocket
from app.core.logging import logger

class ConnectionManager:
    def __init__(self):
        # mechanic_id -> set of active WebSockets (supports multiple browser tabs)
        self.mechanic_connections: Dict[uuid.UUID, Set[WebSocket]] = {}
        # booking_id -> set of active WebSockets (customer / tracker sessions)
        self.customer_booking_connections: Dict[uuid.UUID, Set[WebSocket]] = {}

    async def connect_mechanic(self, mechanic_id: uuid.UUID, websocket: WebSocket):
        await websocket.accept()
        if mechanic_id not in self.mechanic_connections:
            self.mechanic_connections[mechanic_id] = set()
        self.mechanic_connections[mechanic_id].add(websocket)
        logger.info(f"Mechanic WS connected: {mechanic_id} (active tabs: {len(self.mechanic_connections[mechanic_id])})")

    def disconnect_mechanic(self, mechanic_id: uuid.UUID, websocket: WebSocket):
        if mechanic_id in self.mechanic_connections:
            self.mechanic_connections[mechanic_id].discard(websocket)
            if not self.mechanic_connections[mechanic_id]:
                del self.mechanic_connections[mechanic_id]
        logger.info(f"Mechanic WS disconnected: {mechanic_id}")

    async def connect_customer(self, booking_id: uuid.UUID, websocket: WebSocket):
        await websocket.accept()
        if booking_id not in self.customer_booking_connections:
            self.customer_booking_connections[booking_id] = set()
        self.customer_booking_connections[booking_id].add(websocket)
        logger.info(f"Customer WS connected for booking: {booking_id}")

    def disconnect_customer(self, booking_id: uuid.UUID, websocket: WebSocket):
        if booking_id in self.customer_booking_connections:
            self.customer_booking_connections[booking_id].discard(websocket)
            if not self.customer_booking_connections[booking_id]:
                del self.customer_booking_connections[booking_id]
        logger.info(f"Customer WS disconnected for booking: {booking_id}")

    async def send_to_mechanic(self, mechanic_id: uuid.UUID, message: Dict[str, Any]):
        if mechanic_id in self.mechanic_connections:
            dead_sockets = set()
            for ws in list(self.mechanic_connections[mechanic_id]):
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.warning(f"Error sending to mechanic WS {mechanic_id}: {e}")
                    dead_sockets.add(ws)
            for ws in dead_sockets:
                self.disconnect_mechanic(mechanic_id, ws)

    async def broadcast_to_mechanics(self, mechanic_ids: List[uuid.UUID], message: Dict[str, Any]):
        for mid in mechanic_ids:
            await self.send_to_mechanic(mid, message)

    async def send_to_booking_customers(self, booking_id: uuid.UUID, message: Dict[str, Any]):
        if booking_id in self.customer_booking_connections:
            dead_sockets = set()
            for ws in list(self.customer_booking_connections[booking_id]):
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.warning(f"Error sending to customer WS for booking {booking_id}: {e}")
                    dead_sockets.add(ws)
            for ws in dead_sockets:
                self.disconnect_customer(booking_id, ws)

ws_manager = ConnectionManager()
