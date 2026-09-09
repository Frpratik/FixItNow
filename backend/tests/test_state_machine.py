import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.booking import Booking, BookingStatus
from app.db.models.category import ServiceCategory
from app.db.models.user import User
from app.services.state_machine import transition_booking
from app.core.exceptions import BookingStateError

@pytest.mark.asyncio
async def test_legal_lifecycle_transitions(db_session: AsyncSession, sample_customer: User, sample_category: ServiceCategory):
    booking = Booking(
        customer_id=sample_customer.id,
        category_id=sample_category.id,
        description="Fan motor is sparking",
        customer_lat=18.5314,
        customer_lng=73.8446,
        status=BookingStatus.REQUESTED,
    )
    db_session.add(booking)
    await db_session.flush()

    # REQUESTED -> BROADCASTING
    await transition_booking(db_session, booking, BookingStatus.BROADCASTING, sample_customer.id)
    assert booking.status == BookingStatus.BROADCASTING

    # BROADCASTING -> ACCEPTED
    mechanic_id = uuid.uuid4()
    booking.accepted_mechanic_id = mechanic_id
    await transition_booking(db_session, booking, BookingStatus.ACCEPTED, mechanic_id)
    assert booking.status == BookingStatus.ACCEPTED

    # ACCEPTED -> EN_ROUTE
    await transition_booking(db_session, booking, BookingStatus.EN_ROUTE, mechanic_id)
    assert booking.status == BookingStatus.EN_ROUTE

    # EN_ROUTE -> IN_PROGRESS
    await transition_booking(db_session, booking, BookingStatus.IN_PROGRESS, mechanic_id)
    assert booking.status == BookingStatus.IN_PROGRESS

    # IN_PROGRESS -> COMPLETED
    await transition_booking(db_session, booking, BookingStatus.COMPLETED, mechanic_id)
    assert booking.status == BookingStatus.COMPLETED
    await db_session.flush()

    # Verify status history audit records
    from sqlalchemy import select
    from app.db.models.booking_history import BookingStatusHistory
    hist_res = await db_session.execute(
        select(BookingStatusHistory).where(BookingStatusHistory.booking_id == booking.id)
    )
    histories = hist_res.scalars().all()
    assert len(histories) == 5

@pytest.mark.asyncio
async def test_illegal_transition_rejection(db_session: AsyncSession, sample_customer: User, sample_category: ServiceCategory):
    booking = Booking(
        customer_id=sample_customer.id,
        category_id=sample_category.id,
        description="Air conditioner not blowing cold air",
        customer_lat=18.5314,
        customer_lng=73.8446,
        status=BookingStatus.COMPLETED,
    )
    db_session.add(booking)
    await db_session.flush()

    # Attempt illegal transition: COMPLETED -> EN_ROUTE
    with pytest.raises(BookingStateError) as exc_info:
        await transition_booking(db_session, booking, BookingStatus.EN_ROUTE, sample_customer.id)

    assert exc_info.value.code == "BOOKING_INVALID_TRANSITION"
    assert exc_info.value.status_code == 409

@pytest.mark.asyncio
async def test_customer_cancellation_from_broadcasting(db_session: AsyncSession, sample_customer: User, sample_category: ServiceCategory):
    booking = Booking(
        customer_id=sample_customer.id,
        category_id=sample_category.id,
        description="Mixer grinder issue",
        customer_lat=18.5314,
        customer_lng=73.8446,
        status=BookingStatus.BROADCASTING,
    )
    db_session.add(booking)
    await db_session.flush()

    await transition_booking(db_session, booking, BookingStatus.CANCELLED_BY_CUSTOMER, sample_customer.id)
    assert booking.status == BookingStatus.CANCELLED_BY_CUSTOMER
