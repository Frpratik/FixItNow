import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.api.deps import get_current_user, require_customer, require_mechanic
from app.schemas.booking import BookingCreateRequest, BookingResponse, BookingStatusUpdateRequest
from app.schemas.review import ReviewCreateRequest, ReviewResponse
from app.schemas.common import MessageResponse
from app.services.booking_service import BookingService
from app.services.review_service import ReviewService
from app.services.mechanic_booking_service import MechanicBookingService

router = APIRouter(prefix="/bookings", tags=["Bookings"])

@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    req: BookingCreateRequest,
    current_user: User = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    booking = await BookingService.create_booking(db=db, customer_id=current_user.id, req=req)
    return BookingResponse.model_validate(booking)

@router.get("/mine", response_model=List[BookingResponse])
async def list_my_bookings(
    current_user: User = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    return await BookingService.list_customer_bookings(db=db, customer_id=current_user.id)

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking_details(
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await BookingService.get_booking_for_user(db=db, booking_id=booking_id, user=current_user)

@router.post("/{booking_id}/accept", response_model=BookingResponse)
async def accept_booking(
    booking_id: uuid.UUID,
    current_user: User = Depends(require_mechanic),
    db: AsyncSession = Depends(get_db),
):
    return await MechanicBookingService.accept_booking(
        db=db,
        booking_id=booking_id,
        mechanic=current_user
    )

@router.post("/{booking_id}/reject", response_model=MessageResponse)
async def reject_booking(
    booking_id: uuid.UUID,
    current_user: User = Depends(require_mechanic),
    db: AsyncSession = Depends(get_db),
):
    return await MechanicBookingService.reject_booking(
        db=db,
        booking_id=booking_id,
        mechanic_id=current_user.id
    )

@router.patch("/{booking_id}/status", response_model=BookingResponse)
async def update_mechanic_status(
    booking_id: uuid.UUID,
    req: BookingStatusUpdateRequest,
    current_user: User = Depends(require_mechanic),
    db: AsyncSession = Depends(get_db),
):
    return await MechanicBookingService.update_booking_status(
        db=db,
        booking_id=booking_id,
        mechanic_id=current_user.id,
        req=req
    )

@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: uuid.UUID,
    reason: Optional[str] = Query(None),
    current_user: User = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    return await BookingService.cancel_booking_by_customer(
        db=db,
        booking_id=booking_id,
        customer_id=current_user.id,
        reason=reason
    )

@router.post("/{booking_id}/review", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_booking_review(
    booking_id: uuid.UUID,
    req: ReviewCreateRequest,
    current_user: User = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    return await ReviewService.create_review(
        db=db,
        booking_id=booking_id,
        customer_id=current_user.id,
        req=req
    )
