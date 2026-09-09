import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from app.db.models.user import UserRole
from app.schemas.category import CategoryResponse

class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=7, max_length=20)

class CustomerRegisterRequest(UserBase):
    password: str = Field(..., min_length=6, max_length=100)
    role: UserRole = UserRole.CUSTOMER

class MechanicRegisterRequest(UserBase):
    password: str = Field(..., min_length=6, max_length=100)
    role: UserRole = UserRole.MECHANIC
    category_ids: List[uuid.UUID] = Field(..., min_length=1)
    service_radius_km: float = Field(10.0, gt=0, le=100)
    current_lat: Optional[float] = Field(None, ge=-90.0, le=90.0)
    current_lng: Optional[float] = Field(None, ge=-180.0, le=180.0)

class LoginRequest(BaseModel):
    username: str = Field(..., description="Email or phone number")
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class MechanicProfileResponse(BaseModel):
    service_radius_km: float
    is_available: bool
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    rating_avg: float
    jobs_completed: int
    verified: bool
    categories: List[CategoryResponse] = []

    model_config = ConfigDict(from_attributes=True)

class UserResponse(UserBase):
    id: uuid.UUID
    role: UserRole
    created_at: datetime
    mechanic_profile: Optional[MechanicProfileResponse] = None

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
