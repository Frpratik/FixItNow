from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.core.logging import logger

class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

class UnauthorizedError(AppException):
    def __init__(self, message: str = "Authentication required", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="UNAUTHORIZED", message=message, status_code=status.HTTP_401_UNAUTHORIZED, details=details)

class ForbiddenError(AppException):
    def __init__(self, message: str = "Access forbidden", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="FORBIDDEN", message=message, status_code=status.HTTP_403_FORBIDDEN, details=details)

class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="NOT_FOUND", message=message, status_code=status.HTTP_404_NOT_FOUND, details=details)

class ConflictError(AppException):
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(code="CONFLICT", message=message, status_code=status.HTTP_409_CONFLICT, details=details)

class BookingStateError(AppException):
    def __init__(
        self,
        current_status: str,
        requested_status: str,
        allowed_transitions: list[str],
        message: Optional[str] = None
    ):
        msg = message or f"Cannot transition booking from {current_status} to {requested_status}."
        super().__init__(
            code="BOOKING_INVALID_TRANSITION",
            message=msg,
            status_code=status.HTTP_409_CONFLICT,
            details={
                "current_status": current_status,
                "requested_status": requested_status,
                "allowed_transitions": allowed_transitions
            }
        )

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning(f"AppException: {exc.code} - {exc.message}", extra={"extra_data": exc.details})
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    clean_errors = []
    for err in errors:
        loc = " -> ".join([str(p) for p in err.get("loc", []) if p != "body"])
        clean_errors.append({
            "field": loc,
            "message": err.get("msg", "Invalid value"),
            "type": err.get("type")
        })
    logger.warning(f"Validation error on {request.url.path}: {clean_errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed.",
                "details": {"errors": clean_errors}
            }
        }
    )

async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.error(f"Database IntegrityError on {request.url.path}: {str(exc.orig)}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": {
                "code": "DATABASE_INTEGRITY_ERROR",
                "message": "A database constraint violation occurred (e.g. duplicate key or foreign key violation).",
                "details": {"detail": str(exc.orig)}
            }
        }
    )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled exception on {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "details": {}
            }
        }
    )
