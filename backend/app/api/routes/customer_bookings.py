import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.api.deps import get_current_user, require_customer
from app.schemas.booking import BookingCreateRequest, BookingResponse
from app.schemas.review import ReviewCreateRequest, ReviewResponse
from app.services.booking_service import BookingService
from app.services.review_service import ReviewService

router = APIRouter(prefix="/bookings", tags=["Customer Bookings"])

@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    req: BookingCreateRequest,
    current_user: User = Depends(require_customer),
    db: AsyncSession = Depends(get_db),
):
    booking = await BookingService.create_booking(db=db, customer_id=current_user.id, req=req)
    # Background matching will also hook into lifecycle monitor
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
