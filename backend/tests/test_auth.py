import pytest
import uuid
from httpx import AsyncClient
from app.db.models.user import UserRole
from tests.conftest import get_auth_headers

@pytest.mark.asyncio
async def test_customer_registration_success(client: AsyncClient):
    uid = uuid.uuid4().hex[:6]
    res = await client.post(
        "/auth/register",
        json={
            "name": f"Alice {uid}",
            "email": f"alice_{uid}@example.com",
            "phone": f"+9198{uid}000",
            "password": "Password@123",
            "role": "customer",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == f"alice_{uid}@example.com"
    assert data["role"] == "customer"
    assert "password_hash" not in data

@pytest.mark.asyncio
async def test_duplicate_email_registration_conflict(client: AsyncClient, sample_customer):
    res = await client.post(
        "/auth/register",
        json={
            "name": "Duplicate User",
            "email": sample_customer.email,
            "phone": "+919899999999",
            "password": "Password@123",
            "role": "customer",
        },
    )
    assert res.status_code == 409
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "CONFLICT"

@pytest.mark.asyncio
async def test_login_success_and_refresh(client: AsyncClient, sample_customer):
    # Login
    res = await client.post(
        "/auth/login",
        json={
            "username": sample_customer.email,
            "password": "Pass@123",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == sample_customer.email

    # Refresh
    refresh_res = await client.post(
        "/auth/refresh",
        json={"refresh_token": data["refresh_token"]},
    )
    assert refresh_res.status_code == 200
    refresh_data = refresh_res.json()
    assert "access_token" in refresh_data

@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, sample_customer):
    res = await client.post(
        "/auth/login",
        json={
            "username": sample_customer.email,
            "password": "WrongPassword@999",
        },
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHORIZED"

@pytest.mark.asyncio
async def test_role_authorization_guard(client: AsyncClient, sample_customer):
    # Customer attempts to access mechanic console endpoint
    headers = get_auth_headers(sample_customer)
    res = await client.patch(
        "/mechanic/availability",
        json={"is_available": False},
        headers=headers,
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"
