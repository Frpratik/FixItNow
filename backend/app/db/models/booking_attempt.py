import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db.base import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

if TYPE_CHECKING:
    from app.db.models.booking import Booking
    from app.db.models.user import User

class BookingMechanicAttempt(Base):
    __tablename__ = "booking_mechanic_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    mechanic_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    wave: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. NOTIFIED, REJECTED, ACCEPTED, EXPIRED
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    # Relationships
    booking: Mapped["Booking"] = relationship("Booking", back_populates="attempts")
    mechanic: Mapped["User"] = relationship("User", lazy="joined")

Index("ix_attempt_booking_mechanic", BookingMechanicAttempt.booking_id, BookingMechanicAttempt.mechanic_id)
