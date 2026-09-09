import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.category import CategoryResponse

class AvailabilityUpdateRequest(BaseModel):
    is_available: bool

class LocationUpdateRequest(BaseModel):
    current_lat: float = Field(..., ge=-90.0, le=90.0)
    current_lng: float = Field(..., ge=-180.0, le=180.0)

class IncomingJobResponse(BaseModel):
    booking_id: uuid.UUID
    category_id: uuid.UUID
    category_name: str
    description: str
    customer_lat: float
    customer_lng: float
    distance_km: float
    created_at: datetime
    expires_at: Optional[datetime] = None
