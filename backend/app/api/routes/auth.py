from typing import Union
from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models.user import UserRole
from app.schemas.auth import (
    CustomerRegisterRequest,
    MechanicRegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: Union[MechanicRegisterRequest, CustomerRegisterRequest] = Body(...),
    db: AsyncSession = Depends(get_db),
):
    if payload.role == UserRole.MECHANIC:
        if not isinstance(payload, MechanicRegisterRequest):
            # Parse as mechanic
            mechanic_req = MechanicRegisterRequest.model_validate(payload.model_dump())
            return await AuthService.register_mechanic(db, mechanic_req)
        return await AuthService.register_mechanic(db, payload)
    else:
        customer_req = CustomerRegisterRequest.model_validate(payload.model_dump())
        return await AuthService.register_customer(db, customer_req)

@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService.authenticate_user(db, req)

@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    req: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService.refresh_tokens(db, req)
