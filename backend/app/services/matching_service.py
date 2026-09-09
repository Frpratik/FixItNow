import math
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Tuple, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models.booking import Booking, BookingStatus
from app.db.models.booking_attempt import BookingMechanicAttempt
from app.db.models.mechanic_profile import MechanicProfile
from app.db.models.category import ServiceCategory
from app.core.config import settings
from app.core.logging import logger
from app.websocket.manager import ws_manager
from app.services.state_machine import transition_booking

EARTH_RADIUS_KM = 6371.0

def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate the great circle distance between two points in kilometers."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_KM * c

class MatchingService:
    @staticmethod
    async def find_qualified_mechanics(
        db: AsyncSession,
        booking: Booking,
        exclude_mechanic_ids: Optional[Set[uuid.UUID]] = None,
    ) -> List[Tuple[MechanicProfile, float]]:
        exclude_ids = set(exclude_mechanic_ids or set())

        # Load all rejections for this booking
        rej_stmt = select(BookingMechanicAttempt.mechanic_id).where(
            BookingMechanicAttempt.booking_id == booking.id,
            BookingMechanicAttempt.action == "REJECTED"
        )
        rej_res = await db.execute(rej_stmt)
        rejected_ids = set(rej_res.scalars().all())
        exclude_ids.update(rejected_ids)

        # Query all available mechanics who have categories loaded
        stmt = (
            select(MechanicProfile)
            .where(
                MechanicProfile.is_available == True,
                MechanicProfile.current_lat.isnot(None),
                MechanicProfile.current_lng.isnot(None),
            )
            .options(selectinload(MechanicProfile.categories))
        )
        result = await db.execute(stmt)
        all_mechanics = result.scalars().all()

        qualified: List[Tuple[MechanicProfile, float]] = []

        for profile in all_mechanics:
            if profile.user_id in exclude_ids:
                continue

            # Check category matching
            has_cat = any(cat.id == booking.category_id for cat in profile.categories)
            if not has_cat:
                continue

            # Calculate Haversine distance
            dist = haversine_distance(
                booking.customer_lat,
                booking.customer_lng,
                profile.current_lat,
                profile.current_lng,
            )

            # Check radius constraint
            effective_radius = min(settings.MAX_RADIUS_KM, profile.service_radius_km)
            if dist <= effective_radius:
                qualified.append((profile, round(dist, 2)))

        # Sort by distance ascending
        qualified.sort(key=lambda x: x[1])
        return qualified

    @staticmethod
    async def broadcast_wave_1(db: AsyncSession, booking: Booking) -> int:
        qualified = await MatchingService.find_qualified_mechanics(db, booking)
        if not qualified:
            logger.info(f"Wave 1: No qualified mechanics found for booking {booking.id}")
            return 0

        wave_1_mechanics = qualified[: settings.FIRST_WAVE_SIZE]
        category_name = booking.category.name if booking.category else "Electrical Repair"
        expires_at = (booking.created_at + timedelta(minutes=settings.EXPIRY_TIMEOUT_MIN)).isoformat()

        notified_count = 0
        for profile, dist in wave_1_mechanics:
            # Record attempt
            attempt = BookingMechanicAttempt(
                booking_id=booking.id,
                mechanic_id=profile.user_id,
                wave=1,
                action="NOTIFIED",
            )
            db.add(attempt)

            # Dispatch WebSocket payload
            payload = {
                "type": "NEW_JOB",
                "booking_id": str(booking.id),
                "category": category_name,
                "category_id": str(booking.category_id),
                "description": booking.description,
                "customer_lat": booking.customer_lat,
                "customer_lng": booking.customer_lng,
                "distance_km": dist,
                "expires_at": expires_at,
            }
            await ws_manager.send_to_mechanic(profile.user_id, payload)
            notified_count += 1

        await db.commit()
        logger.info(
            f"Wave 1 dispatched for booking {booking.id}: notified {notified_count} mechanics",
            extra={"booking_id": booking.id, "event": "booking_broadcast", "extra_data": {"wave": 1, "count": notified_count}}
        )
        return notified_count

    @staticmethod
    async def broadcast_wave_2(db: AsyncSession, booking: Booking) -> int:
        # Get mechanics already notified in wave 1
        prev_stmt = select(BookingMechanicAttempt.mechanic_id).where(
            BookingMechanicAttempt.booking_id == booking.id
        )
        prev_res = await db.execute(prev_stmt)
        prev_notified_ids = set(prev_res.scalars().all())

        qualified = await MatchingService.find_qualified_mechanics(
            db, booking, exclude_mechanic_ids=prev_notified_ids
        )
        if not qualified:
            logger.info(f"Wave 2: No additional qualified mechanics for booking {booking.id}")
            return 0

        category_name = booking.category.name if booking.category else "Electrical Repair"
        expires_at = (booking.created_at + timedelta(minutes=settings.EXPIRY_TIMEOUT_MIN)).isoformat()

        notified_count = 0
        for profile, dist in qualified:
            attempt = BookingMechanicAttempt(
                booking_id=booking.id,
                mechanic_id=profile.user_id,
                wave=2,
                action="NOTIFIED",
            )
            db.add(attempt)

            payload = {
                "type": "NEW_JOB",
                "booking_id": str(booking.id),
                "category": category_name,
                "category_id": str(booking.category_id),
                "description": booking.description,
                "customer_lat": booking.customer_lat,
                "customer_lng": booking.customer_lng,
                "distance_km": dist,
                "expires_at": expires_at,
            }
            await ws_manager.send_to_mechanic(profile.user_id, payload)
            notified_count += 1

        await db.commit()
        logger.info(
            f"Wave 2 dispatched for booking {booking.id}: notified {notified_count} additional mechanics",
            extra={"booking_id": booking.id, "event": "booking_broadcast", "extra_data": {"wave": 2, "count": notified_count}}
        )
        return notified_count

    @staticmethod
    async def expire_booking(db: AsyncSession, booking: Booking) -> None:
        if booking.status != BookingStatus.BROADCASTING:
            return

        await transition_booking(
            db=db,
            booking=booking,
            new_status=BookingStatus.EXPIRED,
            note="No mechanic accepted before expiry timeout."
        )
        await db.commit()

        # Notify customer via WebSocket
        customer_msg = {
            "type": "BOOKING_STATUS",
            "booking_id": str(booking.id),
            "status": BookingStatus.EXPIRED.value,
            "message": "No mechanic accepted the request in your area.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await ws_manager.send_to_booking_customers(booking.id, customer_msg)

        logger.info(
            f"Booking {booking.id} expired due to timeout",
            extra={"booking_id": booking.id, "event": "booking_expired"}
        )
