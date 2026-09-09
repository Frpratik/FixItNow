import enum
from typing import Optional
from pydantic import BaseModel, Field

class AdminResolutionAction(str, enum.Enum):
    EXPIRE = "expire"
    CANCEL_CUSTOMER = "cancel_customer"
    REBROADCAST = "rebroadcast"
    COMPLETE = "complete"

class ForceResolveRequest(BaseModel):
    action: AdminResolutionAction
    reason: str = Field(..., min_length=3, max_length=500)
