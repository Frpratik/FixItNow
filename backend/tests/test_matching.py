import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.booking import Booking, BookingStatus
from app.db.models.user import User, UserRole
from app.db.models.category import ServiceCategory
from app.db.models.mechanic_profile import MechanicProfile
from app.core.security import get_password_hash
from app.services.matching_service import MatchingService

@pytest.mark.asyncio
async def test_matching_filters_category_and_radius(
    db_session: AsyncSession,
    sample_customer: User,
    sample_category: ServiceCategory
):
    # Customer at Pune (18.5314, 73.8446)
    booking = Booking(
        customer_id=sample_customer.id,
        category_id=sample_category.id,
        description="Fan repair request",
        customer_lat=18.5314,
        customer_lng=73.8446,
        status=BookingStatus.BROADCASTING,
    )
    db_session.add(booking)

    # 1. Nearby qualified mechanic (1.2 km away)
    u1 = User(id=uuid.uuid4(), name="Mech 1 Near", email=f"m1_{uuid.uuid4().hex[:6]}@test.com", phone=f"+91{uuid.uuid4().hex[:10]}", password_hash=get_password_hash("Pass@123"), role=UserRole.MECHANIC)
    db_session.add(u1)
    await db_session.flush()
    p1 = MechanicProfile(user_id=u1.id, service_radius_km=10.0, is_available=True, current_lat=18.5204, current_lng=73.8567)
    p1.categories = [sample_category]
    db_session.add(p1)

    # 2. Far outside radius mechanic (120 km away)
    u2 = User(id=uuid.uuid4(), name="Mech 2 Far", email=f"m2_{uuid.uuid4().hex[:6]}@test.com", phone=f"+91{uuid.uuid4().hex[:10]}", password_hash=get_password_hash("Pass@123"), role=UserRole.MECHANIC)
    db_session.add(u2)
    await db_session.flush()
    p2 = MechanicProfile(user_id=u2.id, service_radius_km=10.0, is_available=True, current_lat=19.0760, current_lng=72.8777)
    p2.categories = [sample_category]
    db_session.add(p2)

    # 3. Offline mechanic (close, but unavailable)
    u3 = User(id=uuid.uuid4(), name="Mech 3 Offline", email=f"m3_{uuid.uuid4().hex[:6]}@test.com", phone=f"+91{uuid.uuid4().hex[:10]}", password_hash=get_password_hash("Pass@123"), role=UserRole.MECHANIC)
    db_session.add(u3)
    await db_session.flush()
    p3 = MechanicProfile(user_id=u3.id, service_radius_km=10.0, is_available=False, current_lat=18.5210, current_lng=73.8560)
    p3.categories = [sample_category]
    db_session.add(p3)

    await db_session.commit()

    qualified = await MatchingService.find_qualified_mechanics(db_session, booking)
    assert len(qualified) >= 1
    qualified_ids = [p.user_id for p, dist in qualified]
    assert u1.id in qualified_ids
    assert u2.id not in qualified_ids
    assert u3.id not in qualified_ids
