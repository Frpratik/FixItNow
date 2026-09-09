import uuid
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload

from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.db.models.mechanic_profile import MechanicProfile
from app.db.models.booking import Booking, BookingStatus
from app.db.models.booking_attempt import BookingMechanicAttempt
from app.api.deps import require_mechanic
from app.schemas.auth import MechanicProfileResponse
from app.schemas.mechanic import AvailabilityUpdateRequest, LocationUpdateRequest, IncomingJobResponse
from app.schemas.booking import BookingResponse, BookingStatusUpdateRequest
from app.schemas.common import MessageResponse
from app.services.mechanic_booking_service import MechanicBookingService
from app.services.matching_service import haversine_distance
from app.core.config import settings
from app.core.exceptions import NotFoundError, ForbiddenError
from app.core.logging import logger

router = APIRouter(prefix="/mechanic", tags=["Mechanic"])

@router.patch("/availability", response_model=MechanicProfileResponse)
async def update_availability(
    req: AvailabilityUpdateRequest,
    current_user: User = Depends(require_mechanic),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(MechanicProfile)
        .where(MechanicProfile.user_id == current_user.id)
        .options(selectinload(MechanicProfile.categories))
    )
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()
    if not profile:
        raise NotFoundError("Mechanic profile not found.")

    profile.is_available = req.is_available
    await db.commit()
    await db.refresh(profile)

    logger.info(f"Mechanic {current_user.id} availability set to {req.is_available}")
    return MechanicProfileResponse.model_validate(profile)

@router.patch("/location", response_model=MechanicProfileResponse)
async def update_location(
    req: LocationUpdateRequest,
    current_user: User = Depends(require_mechanic),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(MechanicProfile)
        .where(MechanicProfile.user_id == current_user.id)
        .options(selectinload(MechanicProfile.categories))
    )
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()
    if not profile:
        raise NotFoundError("Mechanic profile not found.")

    profile.current_lat = req.current_lat
    profile.current_lng = req.current_lng
    await db.commit()
    await db.refresh(profile)

    logger.info(f"Mechanic {current_user.id} location updated to ({req.current_lat}, {req.current_lng})")
    return MechanicProfileResponse.model_validate(profile)

@router.get("/jobs/incoming", response_model=List[IncomingJobResponse])
async def get_incoming_jobs(
    current_user: User = Depends(require_mechanic),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(MechanicProfile)
        .where(MechanicProfile.user_id == current_user.id)
        .options(selectinload(MechanicProfile.categories))
    )
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()
    if not profile or not profile.is_available or profile.current_lat is None or profile.current_lng is None:
        return []

    # Exclude rejected bookings
    rej_stmt = select(BookingMechanicAttempt.booking_id).where(
        BookingMechanicAttempt.mechanic_id == current_user.id,
        BookingMechanicAttempt.action == "REJECTED"
    )
    rej_res = await db.execute(rej_stmt)
    rejected_booking_ids = set(rej_res.scalars().all())

    # Get all BROADCASTING bookings
    cat_ids = [cat.id for cat in profile.categories]
    if not cat_ids:
        return []

    b_stmt = (
        select(Booking)
        .where(
            Booking.status == BookingStatus.BROADCASTING,
            Booking.category_id.in_(cat_ids),
        )
        .options(joinedload(Booking.category))
    )
    b_res = await db.execute(b_stmt)
    bookings = b_res.scalars().all()

    incoming: List[IncomingJobResponse] = []
    effective_radius = min(settings.MAX_RADIUS_KM, profile.service_radius_km)

    for b in bookings:
        if b.id in rejected_booking_ids:
            continue

        dist = haversine_distance(
            b.customer_lat, b.customer_lng,
            profile.current_lat, profile.current_lng
        )
        if dist <= effective_radius:
            expires_at = b.created_at + timedelta(minutes=settings.EXPIRY_TIMEOUT_MIN)
            incoming.append(
                IncomingJobResponse(
                    booking_id=b.id,
                    category_id=b.category_id,
                    category_name=b.category.name if b.category else "Electrical Repair",
                    description=b.description,
                    customer_lat=b.customer_lat,
                    customer_lng=b.customer_lng,
                    distance_km=round(dist, 2),
                    created_at=b.created_at,
                    expires_at=expires_at,
                )
            )

    incoming.sort(key=lambda x: x.distance_km)
    return incoming

@router.get("/jobs/active", response_model=Optional[BookingResponse])
async def get_active_job(
    current_user: User = Depends(require_mechanic),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Booking)
        .where(
            Booking.accepted_mechanic_id == current_user.id,
            Booking.status.in_([BookingStatus.ACCEPTED, BookingStatus.EN_ROUTE, BookingStatus.IN_PROGRESS])
        )
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
        return None
    return BookingResponse.model_validate(booking)

@router.get("/jobs/history", response_model=List[BookingResponse])
async def get_job_history(
    current_user: User = Depends(require_mechanic),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Booking)
        .where(
            Booking.accepted_mechanic_id == current_user.id,
            Booking.status == BookingStatus.COMPLETED
        )
        .options(
            joinedload(Booking.category),
            joinedload(Booking.customer),
            joinedload(Booking.accepted_mechanic),
            selectinload(Booking.status_history),
            selectinload(Booking.review),
        )
        .order_by(Booking.updated_at.desc())
    )
    res = await db.execute(stmt)
    bookings = res.scalars().all()
    return [BookingResponse.model_validate(b) for b in bookings]
