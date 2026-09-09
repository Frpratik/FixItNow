import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload, joinedload

from app.db.models.booking import Booking, BookingStatus
from app.db.models.booking_attempt import BookingMechanicAttempt
from app.db.models.mechanic_profile import MechanicProfile
from app.db.models.user import User, UserRole
from app.schemas.booking import BookingResponse, BookingStatusUpdateRequest
from app.schemas.common import MessageResponse
from app.services.state_machine import transition_booking
from app.services.matching_service import haversine_distance, MatchingService
from app.core.config import settings
from app.core.exceptions import AppException, ForbiddenError, ConflictError, NotFoundError
from app.core.logging import logger
from app.websocket.manager import ws_manager

class MechanicBookingService:
    @staticmethod
    async def accept_booking(
        db: AsyncSession,
        booking_id: uuid.UUID,
        mechanic: User,
    ) -> BookingResponse:
        """
        Concurrency-safe acceptance using PostgreSQL row-level lock (FOR UPDATE).
        Guarantees that when multiple mechanics attempt to accept simultaneously,
        exactly ONE succeeds and all others receive HTTP 409 Conflict.
        """
        # Lock the booking row
        stmt = (
            select(Booking)
            .where(Booking.id == booking_id)
            .with_for_update()
            .options(
                joinedload(Booking.category),
                joinedload(Booking.customer),
                selectinload(Booking.status_history),
                selectinload(Booking.review),
                selectinload(Booking.attempts),
            )
        )
        res = await db.execute(stmt)
        booking = res.scalar_one_or_none()

        if not booking:
            raise NotFoundError("Booking not found.")

        # Concurrency verification: must still be BROADCASTING
        if booking.status != BookingStatus.BROADCASTING or booking.accepted_mechanic_id is not None:
            logger.warning(
                f"Mechanic {mechanic.id} lost accept race for booking {booking_id} (current status: {booking.status.value})",
                extra={"booking_id": booking_id, "mechanic_id": mechanic.id, "event": "accept_race_lost"}
            )
            raise ConflictError(
                message="Booking has already been accepted by another mechanic or is no longer available.",
                details={"current_status": booking.status.value}
            )

        # Verify mechanic eligibility
        prof_stmt = (
            select(MechanicProfile)
            .where(MechanicProfile.user_id == mechanic.id)
            .options(selectinload(MechanicProfile.categories))
        )
        prof_res = await db.execute(prof_stmt)
        profile = prof_res.scalar_one_or_none()

        if not profile:
            raise ForbiddenError("Mechanic profile does not exist.")

        if not profile.is_available:
            raise ConflictError("You must be set to 'Online' to accept incoming bookings.")

        if profile.current_lat is None or profile.current_lng is None:
            raise ConflictError("Current location must be set before accepting bookings.")

        # Verify category matching
        has_cat = any(cat.id == booking.category_id for cat in profile.categories)
        if not has_cat:
            raise ForbiddenError("You are not qualified for this service category.")

        # Verify distance
        dist = haversine_distance(
            booking.customer_lat, booking.customer_lng,
            profile.current_lat, profile.current_lng
        )
        effective_radius = min(settings.MAX_RADIUS_KM, profile.service_radius_km)
        if dist > effective_radius:
            raise ConflictError(f"Customer location ({dist:.1f} km) is outside your service radius ({effective_radius:.1f} km).")

        # Verify not previously rejected
        rej_stmt = select(BookingMechanicAttempt).where(
            BookingMechanicAttempt.booking_id == booking.id,
            BookingMechanicAttempt.mechanic_id == mechanic.id,
            BookingMechanicAttempt.action == "REJECTED"
        )
        rej_res = await db.execute(rej_stmt)
        if rej_res.scalar_one_or_none():
            raise ConflictError("You have already rejected this booking request.")

        # Assign mechanic and transition to ACCEPTED
        booking.accepted_mechanic_id = mechanic.id
        await transition_booking(
            db=db,
            booking=booking,
            new_status=BookingStatus.ACCEPTED,
            changed_by_user_id=mechanic.id,
            note=f"Accepted by mechanic {mechanic.name}"
        )

        # Record attempt
        attempt = BookingMechanicAttempt(
            booking_id=booking.id,
            mechanic_id=mechanic.id,
            wave=1,
            action="ACCEPTED"
        )
        db.add(attempt)

        await db.commit()

        logger.info(
            f"Booking {booking.id} successfully accepted by mechanic {mechanic.id}",
            extra={"booking_id": booking.id, "mechanic_id": mechanic.id, "event": "mechanic_accepted"}
        )

        # Notify Customer via WebSocket
        customer_msg = {
            "type": "BOOKING_ACCEPTED",
            "booking_id": str(booking.id),
            "status": BookingStatus.ACCEPTED.value,
            "mechanic": {
                "id": str(mechanic.id),
                "name": mechanic.name,
                "phone": mechanic.phone,
                "rating_avg": profile.rating_avg,
                "jobs_completed": profile.jobs_completed,
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await ws_manager.send_to_booking_customers(booking.id, customer_msg)

        # Notify other notified mechanics that job is taken
        other_mechanics_stmt = select(BookingMechanicAttempt.mechanic_id).where(
            BookingMechanicAttempt.booking_id == booking.id,
            BookingMechanicAttempt.mechanic_id != mechanic.id
        )
        other_res = await db.execute(other_mechanics_stmt)
        other_ids = list(set(other_res.scalars().all()))

        job_taken_msg = {
            "type": "JOB_TAKEN",
            "booking_id": str(booking.id),
            "category_id": str(booking.category_id),
        }
        await ws_manager.broadcast_to_mechanics(other_ids, job_taken_msg)

        from app.services.booking_service import BookingService
        full_booking = await BookingService.get_booking_raw(db, booking.id)
        return BookingResponse.model_validate(full_booking)

    @staticmethod
    async def reject_booking(
        db: AsyncSession,
        booking_id: uuid.UUID,
        mechanic_id: uuid.UUID,
    ) -> MessageResponse:
        stmt = select(Booking).where(Booking.id == booking_id)
        res = await db.execute(stmt)
        booking = res.scalar_one_or_none()

        if not booking:
            raise NotFoundError("Booking not found.")

        # Persist rejection attempt
        attempt = BookingMechanicAttempt(
            booking_id=booking_id,
            mechanic_id=mechanic_id,
            wave=1,
            action="REJECTED"
        )
        db.add(attempt)
        await db.commit()

        logger.info(
            f"Mechanic {mechanic_id} rejected booking {booking_id}",
            extra={"booking_id": booking_id, "mechanic_id": mechanic_id, "event": "mechanic_rejected"}
        )
        return MessageResponse(message="Booking rejected successfully.")

    @staticmethod
    async def update_booking_status(
        db: AsyncSession,
        booking_id: uuid.UUID,
        mechanic_id: uuid.UUID,
        req: BookingStatusUpdateRequest,
    ) -> BookingResponse:
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

        # Ownership check
        if booking.accepted_mechanic_id != mechanic_id:
            raise ForbiddenError("Only the assigned mechanic can update this booking status.")

        new_status = req.status

        # If mechanic cancels after accepting
        if new_status == BookingStatus.CANCELLED_BY_MECHANIC:
            await transition_booking(
                db=db,
                booking=booking,
                new_status=BookingStatus.CANCELLED_BY_MECHANIC,
                changed_by_user_id=mechanic_id,
                note=req.note or "Cancelled by mechanic"
            )
            # Rebroadcast to other mechanics
            await transition_booking(
                db=db,
                booking=booking,
                new_status=BookingStatus.BROADCASTING,
                changed_by_user_id=mechanic_id,
                note="Rebroadcasting after mechanic cancellation"
            )
            await db.commit()

            # Notify customer
            customer_msg = {
                "type": "BOOKING_STATUS",
                "booking_id": str(booking.id),
                "status": BookingStatus.BROADCASTING.value,
                "message": "Assigned mechanic cancelled. Finding another nearby mechanic...",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await ws_manager.send_to_booking_customers(booking.id, customer_msg)

            # Trigger Wave 1 matching (excluding the cancelled mechanic)
            await MatchingService.broadcast_wave_1(db=db, booking=booking)

        else:
            # EN_ROUTE -> IN_PROGRESS -> COMPLETED
            await transition_booking(
                db=db,
                booking=booking,
                new_status=new_status,
                changed_by_user_id=mechanic_id,
                note=req.note
            )
            await db.commit()

            # Push status update to customer
            customer_msg = {
                "type": "BOOKING_STATUS",
                "booking_id": str(booking.id),
                "status": new_status.value,
                "message": req.note or f"Booking is now {new_status.value}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await ws_manager.send_to_booking_customers(booking.id, customer_msg)

        from app.services.booking_service import BookingService
        full_booking = await BookingService.get_booking_raw(db, booking.id)
        return BookingResponse.model_validate(full_booking)
