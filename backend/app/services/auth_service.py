import uuid
from typing import Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.db.models.user import User, UserRole
from app.db.models.mechanic_profile import MechanicProfile
from app.db.models.category import ServiceCategory
from app.schemas.auth import (
    CustomerRegisterRequest,
    MechanicRegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
)
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.config import settings
from app.core.exceptions import AppException, ConflictError, UnauthorizedError, NotFoundError
from app.core.logging import logger

class AuthService:
    @staticmethod
    async def register_customer(db: AsyncSession, req: CustomerRegisterRequest) -> UserResponse:
        # Check existing email/phone
        stmt = select(User).where(or_(User.email == req.email.lower(), User.phone == req.phone))
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictError("User with this email or phone number already exists.")

        user = User(
            name=req.name.strip(),
            email=req.email.lower().strip(),
            phone=req.phone.strip(),
            password_hash=get_password_hash(req.password),
            role=UserRole.CUSTOMER,
        )
        db.add(user)
        await db.commit()

        # Reload with relationships
        reloaded = await db.execute(
            select(User).where(User.id == user.id).options(
                selectinload(User.mechanic_profile)
            )
        )
        full_user = reloaded.scalar_one()

        logger.info(f"Customer registered: {user.id} ({user.email})", extra={"user_id": user.id, "event": "user_registered"})
        return UserResponse.model_validate(full_user)

    @staticmethod
    async def register_mechanic(db: AsyncSession, req: MechanicRegisterRequest) -> UserResponse:
        # Check existing email/phone
        stmt = select(User).where(or_(User.email == req.email.lower(), User.phone == req.phone))
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ConflictError("User with this email or phone number already exists.")

        # Verify categories exist
        cat_stmt = select(ServiceCategory).where(ServiceCategory.id.in_(req.category_ids))
        cat_result = await db.execute(cat_stmt)
        categories = cat_result.scalars().all()
        if len(categories) != len(req.category_ids):
            raise NotFoundError("One or more selected service categories not found.")

        user = User(
            name=req.name.strip(),
            email=req.email.lower().strip(),
            phone=req.phone.strip(),
            password_hash=get_password_hash(req.password),
            role=UserRole.MECHANIC,
        )
        db.add(user)
        await db.flush()

        profile = MechanicProfile(
            user_id=user.id,
            service_radius_km=req.service_radius_km,
            is_available=True,
            current_lat=req.current_lat,
            current_lng=req.current_lng,
            rating_avg=0.0,
            jobs_completed=0,
            verified=True,
        )
        profile.categories = list(categories)
        db.add(profile)

        await db.commit()

        # Reload with relationships
        reloaded = await db.execute(
            select(User).where(User.id == user.id).options(
                selectinload(User.mechanic_profile).selectinload(MechanicProfile.categories)
            )
        )
        full_user = reloaded.scalar_one()

        logger.info(f"Mechanic registered: {user.id} ({user.email})", extra={"mechanic_id": user.id, "event": "user_registered"})
        return UserResponse.model_validate(full_user)

    @staticmethod
    async def authenticate_user(db: AsyncSession, req: LoginRequest) -> TokenResponse:
        username = req.username.strip().lower()
        stmt = select(User).where(
            or_(User.email == username, User.phone == req.username.strip())
        ).options(
            selectinload(User.mechanic_profile).selectinload(MechanicProfile.categories)
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(req.password, user.password_hash):
            raise UnauthorizedError("Invalid email/phone or password.")

        access_token = create_access_token(subject=user.id, role=user.role.value)
        refresh_token = create_refresh_token(subject=user.id, role=user.role.value)

        logger.info(f"User logged in: {user.id} ({user.role.value})", extra={"user_id": user.id, "event": "user_login"})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user),
        )

    @staticmethod
    async def refresh_tokens(db: AsyncSession, req: RefreshTokenRequest) -> TokenResponse:
        payload = decode_token(req.refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid or expired refresh token.")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise UnauthorizedError("Token missing subject identifier.")

        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise UnauthorizedError("Invalid user ID format in token.")

        stmt = select(User).where(User.id == user_id).options(
            selectinload(User.mechanic_profile).selectinload(MechanicProfile.categories)
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise UnauthorizedError("User associated with token not found.")

        new_access_token = create_access_token(subject=user.id, role=user.role.value)
        new_refresh_token = create_refresh_token(subject=user.id, role=user.role.value)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user),
        )
