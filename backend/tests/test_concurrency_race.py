import asyncio
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.main import app
from app.db.models.user import User, UserRole
from app.db.models.category import ServiceCategory
from app.db.models.mechanic_profile import MechanicProfile
from app.db.models.booking import Booking, BookingStatus
from app.core.security import get_password_hash
from tests.conftest import TestingSessionLocal, get_auth_headers

@pytest.mark.asyncio
async def test_concurrent_mechanic_accept_race():
    """
    Mandatory Concurrency Race Test:
    Spawns two concurrent tasks attempting to accept the exact same BROADCASTING booking simultaneously.
    Verifies that PostgreSQL row-level locking guarantees:
    - Exactly ONE mechanic receives HTTP 200 OK (the winner)
    - The losing mechanic receives HTTP 409 Conflict
    - The booking in the database is assigned to exactly ONE mechanic
    """
    async with TestingSessionLocal() as db:
        # 1. Setup Category
        cat = ServiceCategory(
            id=uuid.uuid4(),
            name=f"Race Test Cat {uuid.uuid4().hex[:6]}",
            description="Concurrency test category"
        )
        db.add(cat)

        # 2. Setup Customer & Booking
        customer = User(
            id=uuid.uuid4(),
            name="Race Customer",
            email=f"race_cust_{uuid.uuid4().hex[:6]}@test.local",
            phone=f"+9188{uuid.uuid4().hex[:8]}",
            password_hash=get_password_hash("Pass@123"),
            role=UserRole.CUSTOMER,
        )
        db.add(customer)
        await db.flush()

        booking = Booking(
            id=uuid.uuid4(),
            customer_id=customer.id,
            category_id=cat.id,
            description="Concurrent race booking test",
            customer_lat=18.5314,
            customer_lng=73.8446,
            status=BookingStatus.BROADCASTING,
        )
        db.add(booking)

        # 3. Setup Mechanic A
        mech_a = User(
            id=uuid.uuid4(),
            name="Mechanic A (Racer 1)",
            email=f"racer_a_{uuid.uuid4().hex[:6]}@test.local",
            phone=f"+9177{uuid.uuid4().hex[:8]}",
            password_hash=get_password_hash("Pass@123"),
            role=UserRole.MECHANIC,
        )
        db.add(mech_a)
        await db.flush()
        prof_a = MechanicProfile(
            user_id=mech_a.id,
            service_radius_km=10.0,
            is_available=True,
            current_lat=18.5204,
            current_lng=73.8567,
        )
        prof_a.categories = [cat]
        db.add(prof_a)

        # 4. Setup Mechanic B
        mech_b = User(
            id=uuid.uuid4(),
            name="Mechanic B (Racer 2)",
            email=f"racer_b_{uuid.uuid4().hex[:6]}@test.local",
            phone=f"+9177{uuid.uuid4().hex[:8]}",
            password_hash=get_password_hash("Pass@123"),
            role=UserRole.MECHANIC,
        )
        db.add(mech_b)
        await db.flush()
        prof_b = MechanicProfile(
            user_id=mech_b.id,
            service_radius_km=10.0,
            is_available=True,
            current_lat=18.5210,
            current_lng=73.8570,
        )
        prof_b.categories = [cat]
        db.add(prof_b)

        await db.commit()

        booking_id = booking.id
        mech_a_user = mech_a
        mech_b_user = mech_b

    # Define the concurrent client request function
    async def try_accept(user: User):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            headers = get_auth_headers(user)
            return await ac.post(f"/bookings/{booking_id}/accept", headers=headers)

    # Launch both accept requests concurrently
    res_a, res_b = await asyncio.gather(
        try_accept(mech_a_user),
        try_accept(mech_b_user)
    )

    statuses = [res_a.status_code, res_b.status_code]

    # CRITICAL VERIFICATIONS:
    # 1. Exactly one response is 200 OK
    assert statuses.count(200) == 1, f"Expected exactly one 200, got: {statuses}"
    # 2. Exactly one response is 409 Conflict
    assert statuses.count(409) == 1, f"Expected exactly one 409, got: {statuses}"

    # Verify conflict error payload on the loser
    loser_res = res_a if res_a.status_code == 409 else res_b
    assert loser_res.json()["error"]["code"] == "CONFLICT"

    # Verify Database state
    async with TestingSessionLocal() as verify_db:
        stmt = select(Booking).where(Booking.id == booking_id)
        res = await verify_db.execute(stmt)
        final_booking = res.scalar_one()

        assert final_booking.status == BookingStatus.ACCEPTED
        assert final_booking.accepted_mechanic_id in [mech_a_user.id, mech_b_user.id]
