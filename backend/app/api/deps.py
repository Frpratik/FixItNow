import uuid
from typing import AsyncGenerator, Callable, List, Optional
from fastapi import Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models.user import User, UserRole
from app.db.models.mechanic_profile import MechanicProfile
from app.core.security import decode_token
from app.core.exceptions import UnauthorizedError, ForbiddenError

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(None),
    token_query: Optional[str] = Query(None, alias="token"),
) -> User:
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    elif token_query:
        token = token_query

    if not token:
        raise UnauthorizedError(message="Authentication credentials were not provided")

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedError(message="Invalid or expired access token")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError(message="Token missing subject identifier")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedError(message="Invalid user ID format in token")

    query = select(User).where(User.id == user_id).options(
        selectinload(User.mechanic_profile).selectinload(MechanicProfile.categories)
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedError(message="User associated with token not found")

    return user

def require_role(*allowed_roles: UserRole) -> Callable:
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenError(
                message=f"Action forbidden for role '{current_user.role.value}'. Allowed: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return role_checker

# Predefined role dependencies
require_customer = require_role(UserRole.CUSTOMER)
require_mechanic = require_role(UserRole.MECHANIC)
require_admin = require_role(UserRole.ADMIN)
require_any_authenticated = require_role(UserRole.CUSTOMER, UserRole.MECHANIC, UserRole.ADMIN)
