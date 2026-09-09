import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.booking import Booking, BookingStatus
from app.db.models.user import User
from app.db.models.category import ServiceCategory
from tests.conftest import get_auth_headers

@pytest.mark.asyncio
async def test_admin_force_resolve_booking(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_admin: User,
    sample_customer: User,
    sample_category: ServiceCategory,
):
    booking = Booking(
        id=uuid.uuid4(),
        customer_id=sample_customer.id,
        category_id=sample_category.id,
        description="Stuck booking test",
        customer_lat=18.5314,
        customer_lng=73.8446,
        status=BookingStatus.BROADCASTING,
    )
    db_session.add(booking)
    await db_session.commit()

    headers = get_auth_headers(sample_admin)
    res = await client.post(
        f"/admin/bookings/{booking.id}/force-resolve",
        json={
            "action": "expire",
            "reason": "Test admin expired stuck booking",
        },
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "EXPIRED"

@pytest.mark.asyncio
async def test_non_admin_cannot_access_admin_routes(
    client: AsyncClient,
    sample_customer: User,
):
    headers = get_auth_headers(sample_customer)
    res = await client.get("/admin/users", headers=headers)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"
