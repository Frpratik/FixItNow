import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload

from app.db.models.booking import Booking, BookingStatus
from app.db.models.booking_history import BookingStatusHistory
from app.db.models.category import ServiceCategory
from app.db.models.user import User, UserRole
from app.schemas.booking import BookingCreateRequest, BookingResponse
from app.services.state_machine import transition_booking
from app.core.exceptions import AppException, ForbiddenError, ConflictError, NotFoundError
from app.core.logging import logger

class BookingService:
    @staticmethod
    async def create_booking(
        db: AsyncSession,
        customer_id: uuid.UUID,
        req: BookingCreateRequest
    ) -> Booking:
        # Check category exists
        cat_stmt = select(ServiceCategory).where(ServiceCategory.id == req.category_id)
        cat_res = await db.execute(cat_stmt)
        category = cat_res.scalar_one_or_none()
        if not category:
            raise NotFoundError("Selected service category does not exist.")

        # Create booking in REQUESTED state
        booking = Booking(
            customer_id=customer_id,
            category_id=req.category_id,
            description=req.description.strip(),
            customer_lat=req.customer_lat,
            customer_lng=req.customer_lng,
            status=BookingStatus.REQUESTED,
            scheduled_at=req.scheduled_at,
        )
        db.add(booking)
        await db.flush()

        # Initial history
        initial_history = BookingStatusHistory(
            booking_id=booking.id,
            status=BookingStatus.REQUESTED.value,
            note="Booking created by customer",
            changed_by_user_id=customer_id
        )
        db.add(initial_history)

        # Transition to BROADCASTING
        await transition_booking(
            db=db,
            booking=booking,
            new_status=BookingStatus.BROADCASTING,
            changed_by_user_id=customer_id,
            note="Broadcast initiated for nearby mechanics"
        )

        await db.commit()

        # Reload full details
        full_booking = await BookingService.get_booking_raw(db, booking.id)
        logger.info(
            f"Booking created and broadcasting: {booking.id}",
            extra={"booking_id": booking.id, "user_id": customer_id, "event": "booking_created"}
        )
        return full_booking

    @staticmethod
    async def get_booking_raw(db: AsyncSession, booking_id: uuid.UUID) -> Optional[Booking]:
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
        return res.scalar_one_or_none()

    @staticmethod
    async def get_booking_for_user(
        db: AsyncSession,
        booking_id: uuid.UUID,
        user: User
    ) -> BookingResponse:
        booking = await BookingService.get_booking_raw(db, booking_id)
        if not booking:
            raise NotFoundError("Booking not found.")

        # Access check: customer owner, accepted mechanic, or admin
        if user.role == UserRole.ADMIN:
            pass
        elif user.role == UserRole.CUSTOMER and booking.customer_id != user.id:
            raise ForbiddenError("You do not have permission to view this booking.")
        elif user.role == UserRole.MECHANIC and booking.accepted_mechanic_id != user.id and booking.status != BookingStatus.BROADCASTING:
            raise ForbiddenError("You do not have permission to view this booking.")

        return BookingResponse.model_validate(booking)

    @staticmethod
    async def list_customer_bookings(
        db: AsyncSession,
        customer_id: uuid.UUID
    ) -> List[BookingResponse]:
        stmt = (
            select(Booking)
            .where(Booking.customer_id == customer_id)
            .options(
                joinedload(Booking.category),
                joinedload(Booking.customer),
                joinedload(Booking.accepted_mechanic),
                selectinload(Booking.status_history),
                selectinload(Booking.review),
            )
            .order_by(Booking.created_at.desc())
        )
        res = await db.execute(stmt)
        bookings = res.scalars().all()
        return [BookingResponse.model_validate(b) for b in bookings]

    @staticmethod
    async def cancel_booking_by_customer(
        db: AsyncSession,
        booking_id: uuid.UUID,
        customer_id: uuid.UUID,
        reason: Optional[str] = None
    ) -> BookingResponse:
        booking = await BookingService.get_booking_raw(db, booking_id)
        if not booking:
            raise NotFoundError("Booking not found.")

        if booking.customer_id != customer_id:
            raise ForbiddenError("You can only cancel your own bookings.")

        if booking.status not in (BookingStatus.REQUESTED, BookingStatus.BROADCASTING):
            raise ConflictError(
                f"Cannot cancel booking in '{booking.status.value}' state. Cancellation is only allowed before mechanic acceptance."
            )

        await transition_booking(
            db=db,
            booking=booking,
            new_status=BookingStatus.CANCELLED_BY_CUSTOMER,
            changed_by_user_id=customer_id,
            note=reason or "Cancelled by customer"
        )
        await db.commit()

        reloaded = await BookingService.get_booking_raw(db, booking.id)
        logger.info(
            f"Booking {booking.id} cancelled by customer {customer_id}",
            extra={"booking_id": booking.id, "user_id": customer_id, "event": "booking_cancelled"}
        )
        return BookingResponse.model_validate(reloaded)
