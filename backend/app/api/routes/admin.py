import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload

from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.db.models.mechanic_profile import MechanicProfile
from app.db.models.booking import Booking, BookingStatus
from app.api.deps import require_admin
from app.schemas.auth import UserResponse
from app.schemas.booking import BookingResponse
from app.schemas.admin import ForceResolveRequest, AdminResolutionAction
from app.services.state_machine import transition_booking
from app.services.matching_service import MatchingService
from app.services.booking_service import BookingService
from app.core.exceptions import NotFoundError, ConflictError
from app.core.logging import logger
from app.websocket.manager import ws_manager

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    role: Optional[UserRole] = Query(None),
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(User)
        .options(
            selectinload(User.mechanic_profile).selectinload(MechanicProfile.categories)
        )
        .order_by(User.created_at.desc())
    )
    if role:
        stmt = stmt.where(User.role == role)

    res = await db.execute(stmt)
    users = res.scalars().all()
    return [UserResponse.model_validate(u) for u in users]

@router.get("/bookings", response_model=List[BookingResponse])
async def list_all_bookings(
    status: Optional[BookingStatus] = Query(None),
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Booking)
        .options(
            joinedload(Booking.category),
            joinedload(Booking.customer),
            joinedload(Booking.accepted_mechanic),
            selectinload(Booking.status_history),
            selectinload(Booking.review),
        )
        .order_by(Booking.created_at.desc())
    )
    if status:
        stmt = stmt.where(Booking.status == status)

    res = await db.execute(stmt)
    bookings = res.scalars().all()
    return [BookingResponse.model_validate(b) for b in bookings]

@router.post("/bookings/{booking_id}/force-resolve", response_model=BookingResponse)
async def force_resolve_booking(
    booking_id: uuid.UUID,
    req: ForceResolveRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Booking)
        .where(Booking.id == booking_id)
        .options(
            joinedload(Booking.category),
            joinedload(Booking.customer),
            joinedload(Booking.accepted_mechanic),
            selectinload(Booking.status_history),
            selectinload(Booking.review),
        )
    )
    res = await db.execute(stmt)
    booking = res.scalar_one_or_none()

    if not booking:
        raise NotFoundError("Booking not found.")

    target_status_map = {
        AdminResolutionAction.EXPIRE: BookingStatus.EXPIRED,
        AdminResolutionAction.CANCEL_CUSTOMER: BookingStatus.CANCELLED_BY_CUSTOMER,
        AdminResolutionAction.REBROADCAST: BookingStatus.BROADCASTING,
        AdminResolutionAction.COMPLETE: BookingStatus.COMPLETED,
    }

    target_status = target_status_map[req.action]
    note = f"Admin force-resolved: {req.reason.strip()}"

    await transition_booking(
        db=db,
        booking=booking,
        new_status=target_status,
        changed_by_user_id=current_admin.id,
        note=note,
        is_admin_override=True,
    )
    await db.commit()

    # Notify customer via WebSocket
    customer_msg = {
        "type": "BOOKING_STATUS",
        "booking_id": str(booking.id),
        "status": target_status.value,
        "message": f"Admin resolution applied: {req.reason}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await ws_manager.send_to_booking_customers(booking.id, customer_msg)

    # If rebroadcast, trigger wave 1
    if target_status == BookingStatus.BROADCASTING:
        await MatchingService.broadcast_wave_1(db, booking)

    reloaded = await BookingService.get_booking_raw(db, booking.id)
    logger.info(
        f"Admin {current_admin.id} force-resolved booking {booking.id} to {target_status.value}",
        extra={"booking_id": booking.id, "user_id": current_admin.id, "event": "admin_force_resolve"}
    )
    return BookingResponse.model_validate(reloaded)
