import asyncio
import uuid
import sys
import os
import pytest
import pytest_asyncio

# Ensure app is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.config import settings
from app.core.security import get_password_hash, create_access_token
from app.db.models.user import User, UserRole
from app.db.models.category import ServiceCategory
from app.db.models.mechanic_profile import MechanicProfile

settings.TESTING = True

test_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    poolclass=NullPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        async with TestingSessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

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
        email=f"customer_{uid.hex[:6]}@example.com",
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
        email=f"mechanic_{uid.hex[:6]}@example.com",
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
        email=f"admin_{uid.hex[:6]}@example.com",
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
