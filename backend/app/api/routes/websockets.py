import uuid
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.db.models.user import User, UserRole
from app.db.models.booking import Booking
from app.core.security import decode_token
from app.core.logging import logger
from app.websocket.manager import ws_manager

router = APIRouter(prefix="/ws", tags=["WebSockets"])

async def get_user_from_token(token: Optional[str]) -> Optional[User]:
    if not token:
        return None
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None
    user_id_str = payload.get("sub")
    if not user_id_str:
        return None
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        return None

    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.id == user_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

@router.websocket("/mechanic/{mechanic_id}")
async def mechanic_websocket_endpoint(
    websocket: WebSocket,
    mechanic_id: uuid.UUID,
    token: Optional[str] = Query(None),
):
    user = await get_user_from_token(token)
    if not user or user.id != mechanic_id or user.role != UserRole.MECHANIC:
        logger.warning(f"Unauthorized mechanic WS connection rejected: {mechanic_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws_manager.connect_mechanic(mechanic_id, websocket)
    try:
        while True:
            # Keep socket alive and accept ping/pong or client messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect_mechanic(mechanic_id, websocket)
    except Exception as e:
        logger.error(f"Error in mechanic WS connection {mechanic_id}: {e}")
        ws_manager.disconnect_mechanic(mechanic_id, websocket)

@router.websocket("/customer/{booking_id}")
async def customer_websocket_endpoint(
    websocket: WebSocket,
    booking_id: uuid.UUID,
    token: Optional[str] = Query(None),
):
    user = await get_user_from_token(token)
    if not user:
        logger.warning(f"Unauthenticated customer WS connection rejected for booking {booking_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Check booking access
    async with AsyncSessionLocal() as db:
        stmt = select(Booking).where(Booking.id == booking_id)
        res = await db.execute(stmt)
        booking = res.scalar_one_or_none()

        if not booking:
            logger.warning(f"Customer WS connection rejected: booking {booking_id} not found")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        if user.role != UserRole.ADMIN and booking.customer_id != user.id:
            logger.warning(f"Forbidden customer WS connection rejected for user {user.id} on booking {booking_id}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await ws_manager.connect_customer(booking_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect_customer(booking_id, websocket)
    except Exception as e:
        logger.error(f"Error in customer WS connection for booking {booking_id}: {e}")
        ws_manager.disconnect_customer(booking_id, websocket)
