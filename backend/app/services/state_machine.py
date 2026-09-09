import uuid
from typing import Dict, List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.booking import Booking, BookingStatus
from app.db.models.booking_history import BookingStatusHistory
from app.core.exceptions import BookingStateError
from app.core.logging import logger

# Legal state transitions map
LEGAL_TRANSITIONS: Dict[BookingStatus, Set[BookingStatus]] = {
    BookingStatus.REQUESTED: {
        BookingStatus.BROADCASTING,
        BookingStatus.CANCELLED_BY_CUSTOMER,
    },
    BookingStatus.BROADCASTING: {
        BookingStatus.ACCEPTED,
        BookingStatus.CANCELLED_BY_CUSTOMER,
        BookingStatus.EXPIRED,
    },
    BookingStatus.ACCEPTED: {
        BookingStatus.EN_ROUTE,
        BookingStatus.CANCELLED_BY_MECHANIC,
    },
    BookingStatus.EN_ROUTE: {
        BookingStatus.IN_PROGRESS,
    },
    BookingStatus.IN_PROGRESS: {
        BookingStatus.COMPLETED,
    },
    BookingStatus.CANCELLED_BY_MECHANIC: {
        BookingStatus.BROADCASTING,
    },
    # Terminal states have no standard user transitions
    BookingStatus.COMPLETED: set(),
    BookingStatus.CANCELLED_BY_CUSTOMER: set(),
    BookingStatus.EXPIRED: set(),
}

async def transition_booking(
    db: AsyncSession,
    booking: Booking,
    new_status: BookingStatus,
    changed_by_user_id: Optional[uuid.UUID] = None,
    note: Optional[str] = None,
    is_admin_override: bool = False,
) -> Booking:
    current_status = booking.status

    if current_status == new_status:
        return booking

    allowed = LEGAL_TRANSITIONS.get(current_status, set())
    if not is_admin_override and new_status not in allowed:
        logger.warning(
            f"Illegal booking state transition attempted: {current_status} -> {new_status} for booking {booking.id}",
            extra={"booking_id": booking.id, "event": "illegal_transition_attempt"}
        )
        raise BookingStateError(
            current_status=current_status.value if isinstance(current_status, BookingStatus) else str(current_status),
            requested_status=new_status.value if isinstance(new_status, BookingStatus) else str(new_status),
            allowed_transitions=[s.value for s in allowed]
        )

    # State specific modifications
    if new_status == BookingStatus.BROADCASTING and current_status == BookingStatus.CANCELLED_BY_MECHANIC:
        booking.accepted_mechanic_id = None

    booking.status = new_status

    # Create immutable audit record
    history_entry = BookingStatusHistory(
        booking_id=booking.id,
        status=new_status.value,
        note=note,
        changed_by_user_id=changed_by_user_id
    )
    db.add(history_entry)

    logger.info(
        f"Booking {booking.id} transitioned {current_status.value} -> {new_status.value} by user {changed_by_user_id}",
        extra={
            "booking_id": booking.id,
            "user_id": changed_by_user_id,
            "event": "booking_transitioned",
            "extra_data": {"from": current_status.value, "to": new_status.value, "note": note}
        }
    )

    return booking
