import asyncio
import uuid
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.config import settings
from app.core.security import get_password_hash, create_access_token
from app.db.models.user import User, UserRole
from app.db.models.category import ServiceCategory
from app.db.models.mechanic_profile import MechanicProfile
from app.db.models.booking import Booking, BookingStatus

# Use local test database URL or test schema
TEST_DATABASE_URL = settings.DATABASE_URL

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Keep schema intact for test inspectability

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def sample_category(db_session: AsyncSession) -> ServiceCategory:
    cat_id = uuid.uuid4()
    cat = ServiceCategory(
        id=cat_id,
        name=f"Fan Repair Test {cat_id.hex[:6]}",
        description="Ceiling fan test category"
    )
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)
    return cat

@pytest_asyncio.fixture
async def sample_customer(db_session: AsyncSession) -> User:
    uid = uuid.uuid4()
    user = User(
        id=uid,
        name="Test Customer",
        email=f"customer_{uid.hex[:6]}@test.local",
        phone=f"+9198{uid.hex[:8]}",
        password_hash=get_password_hash("Pass@123"),
        role=UserRole.CUSTOMER,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def sample_mechanic(db_session: AsyncSession, sample_category: ServiceCategory) -> User:
    uid = uuid.uuid4()
    user = User(
        id=uid,
        name="Test Mechanic",
        email=f"mechanic_{uid.hex[:6]}@test.local",
        phone=f"+9197{uid.hex[:8]}",
        password_hash=get_password_hash("Pass@123"),
        role=UserRole.MECHANIC,
    )
    db_session.add(user)
    await db_session.flush()

    profile = MechanicProfile(
        user_id=user.id,
        service_radius_km=10.0,
        is_available=True,
        current_lat=18.5204,
        current_lng=73.8567,
        rating_avg=5.0,
        jobs_completed=10,
        verified=True,
    )
    profile.categories = [sample_category]
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def sample_admin(db_session: AsyncSession) -> User:
    uid = uuid.uuid4()
    user = User(
        id=uid,
        name="Test Admin",
        email=f"admin_{uid.hex[:6]}@test.local",
        phone=f"+9199{uid.hex[:8]}",
        password_hash=get_password_hash("Pass@123"),
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

def get_auth_headers(user: User) -> dict:
    token = create_access_token(subject=user.id, role=user.role.value)
    return {"Authorization": f"Bearer {token}"}
