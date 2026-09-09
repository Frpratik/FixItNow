from typing import Any, Dict, Optional
from pydantic import BaseModel

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail

class MessageResponse(BaseModel):
    message: str
    success: bool = True
