import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.booking import Booking, BookingStatus
from app.db.models.user import User
from app.db.models.category import ServiceCategory
from tests.conftest import get_auth_headers

@pytest.mark.asyncio
async def test_review_completed_booking_success(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_customer: User,
    sample_mechanic: User,
    sample_category: ServiceCategory,
):
    # Create completed booking
    booking = Booking(
        id=uuid.uuid4(),
        customer_id=sample_customer.id,
        category_id=sample_category.id,
        accepted_mechanic_id=sample_mechanic.id,
        description="Washing machine drum fix completed",
        customer_lat=18.5314,
        customer_lng=73.8446,
        status=BookingStatus.COMPLETED,
    )
    db_session.add(booking)
    await db_session.commit()

    headers = get_auth_headers(sample_customer)
    res = await client.post(
        f"/bookings/{booking.id}/review",
        json={"rating": 5, "comment": "Excellent and prompt electrical fix!"},
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["rating"] == 5
    assert data["booking_id"] == str(booking.id)

@pytest.mark.asyncio
async def test_review_incomplete_booking_rejected(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_customer: User,
    sample_mechanic: User,
    sample_category: ServiceCategory,
):
    # Booking still in progress
    booking = Booking(
        id=uuid.uuid4(),
        customer_id=sample_customer.id,
        category_id=sample_category.id,
        accepted_mechanic_id=sample_mechanic.id,
        description="Switchboard repair in progress",
        customer_lat=18.5314,
        customer_lng=73.8446,
        status=BookingStatus.IN_PROGRESS,
    )
    db_session.add(booking)
    await db_session.commit()

    headers = get_auth_headers(sample_customer)
    res = await client.post(
        f"/bookings/{booking.id}/review",
        json={"rating": 4},
        headers=headers,
    )
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "CONFLICT"
