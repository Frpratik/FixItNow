import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, joinedload

from app.db.session import AsyncSessionLocal
from app.db.models.booking import Booking, BookingStatus
from app.db.models.booking_attempt import BookingMechanicAttempt
from app.services.matching_service import MatchingService
from app.core.config import settings
from app.core.logging import logger

class BookingMonitor:
    def __init__(self, check_interval_sec: float = 5.0):
        self.check_interval_sec = check_interval_sec
        self.is_running = False
        self._task: asyncio.Task | None = None

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._task = asyncio.create_task(self._monitor_loop())
            logger.info("BookingMonitor background task started")

    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            logger.info("BookingMonitor background task stopped")

    async def _monitor_loop(self):
        while self.is_running:
            try:
                await self.check_broadcasting_bookings()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in BookingMonitor loop: {e}", exc_info=True)

            try:
                await asyncio.sleep(self.check_interval_sec)
            except asyncio.CancelledError:
                break

    async def check_broadcasting_bookings(self):
        async with AsyncSessionLocal() as db:
            now = datetime.now(timezone.utc)
            # Find all BROADCASTING bookings
            stmt = (
                select(Booking)
                .where(Booking.status == BookingStatus.BROADCASTING)
                .options(
                    joinedload(Booking.category),
                    selectinload(Booking.attempts),
                )
            )
            res = await db.execute(stmt)
            bookings = res.scalars().all()

            for booking in bookings:
                elapsed_sec = (now - booking.created_at).total_seconds()

                # Check Expiry
                if elapsed_sec >= (settings.EXPIRY_TIMEOUT_MIN * 60):
                    logger.info(f"Monitor: Booking {booking.id} reached expiry threshold ({elapsed_sec:.1f}s)")
                    await MatchingService.expire_booking(db, booking)
                    continue

                # Check Wave 2 condition: elapsed >= FIRST_WAVE_TIMEOUT_SEC and no wave 2 attempts yet
                has_wave_2 = any(att.wave >= 2 for att in booking.attempts)
                if elapsed_sec >= settings.FIRST_WAVE_TIMEOUT_SEC and not has_wave_2:
                    logger.info(f"Monitor: Booking {booking.id} reached Wave 2 threshold ({elapsed_sec:.1f}s)")
                    await MatchingService.broadcast_wave_2(db, booking)

booking_monitor = BookingMonitor()
