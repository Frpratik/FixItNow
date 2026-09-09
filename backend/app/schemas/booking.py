import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.db.models.booking import BookingStatus
from app.schemas.category import CategoryResponse
from app.schemas.review import ReviewResponse

class BookingStatusHistoryResponse(BaseModel):
    id: uuid.UUID
    status: str
    changed_at: datetime
    note: Optional[str] = None
    changed_by_user_id: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True)

class BookingCreateRequest(BaseModel):
    category_id: uuid.UUID
    description: str = Field(..., min_length=5, max_length=2000)
    customer_lat: float = Field(..., ge=-90.0, le=90.0)
    customer_lng: float = Field(..., ge=-180.0, le=180.0)
    scheduled_at: Optional[datetime] = None

class BookingStatusUpdateRequest(BaseModel):
    status: BookingStatus
    note: Optional[str] = None

class UserSummaryResponse(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    email: str
    rating_avg: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class BookingResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    category_id: uuid.UUID
    description: str
    customer_lat: float
    customer_lng: float
    status: BookingStatus
    accepted_mechanic_id: Optional[uuid.UUID] = None
    scheduled_at: Optional[datetime] = None
    price_estimate: Optional[float] = None
    final_price: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    category: Optional[CategoryResponse] = None
    customer: Optional[UserSummaryResponse] = None
    accepted_mechanic: Optional[UserSummaryResponse] = None
    status_history: List[BookingStatusHistoryResponse] = []
    review: Optional[ReviewResponse] = None

    model_config = ConfigDict(from_attributes=True)
