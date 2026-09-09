from app.schemas.common import ErrorDetail, ErrorResponse, MessageResponse
from app.schemas.category import CategoryBase, CategoryCreateRequest, CategoryResponse
from app.schemas.auth import (
    UserBase,
    CustomerRegisterRequest,
    MechanicRegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    MechanicProfileResponse,
    UserResponse,
    TokenResponse,
)
from app.schemas.review import ReviewCreateRequest, ReviewResponse
from app.schemas.booking import (
    BookingCreateRequest,
    BookingStatusUpdateRequest,
    BookingResponse,
    BookingStatusHistoryResponse,
    UserSummaryResponse,
)
from app.schemas.mechanic import AvailabilityUpdateRequest, LocationUpdateRequest, IncomingJobResponse
from app.schemas.admin import AdminResolutionAction, ForceResolveRequest

__all__ = [
    "ErrorDetail",
    "ErrorResponse",
    "MessageResponse",
    "CategoryBase",
    "CategoryCreateRequest",
    "CategoryResponse",
    "UserBase",
    "CustomerRegisterRequest",
    "MechanicRegisterRequest",
    "LoginRequest",
    "RefreshTokenRequest",
    "MechanicProfileResponse",
    "UserResponse",
    "TokenResponse",
    "ReviewCreateRequest",
    "ReviewResponse",
    "BookingCreateRequest",
    "BookingStatusUpdateRequest",
    "BookingResponse",
    "BookingStatusHistoryResponse",
    "UserSummaryResponse",
    "AvailabilityUpdateRequest",
    "LocationUpdateRequest",
    "IncomingJobResponse",
    "AdminResolutionAction",
    "ForceResolveRequest",
]
