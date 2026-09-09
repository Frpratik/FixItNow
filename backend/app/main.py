from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    integrity_error_handler,
    global_exception_handler,
)
from app.api.routes import auth, categories, health, customer_bookings, websockets, mechanic, admin

from app.background.booking_monitor import booking_monitor

# Setup structured logging
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting FixItNow API in {settings.ENVIRONMENT} mode...")
    if not settings.TESTING:
        booking_monitor.start()
    yield
    logger.info("Shutting down FixItNow API...")
    if not settings.TESTING:
        await booking_monitor.stop()

app = FastAPI(
    title="FixItNow API",
    description="Production-Grade On-Demand Appliance Repair Marketplace API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Include core routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(customer_bookings.router)
app.include_router(mechanic.router)
app.include_router(admin.router)
app.include_router(websockets.router)
