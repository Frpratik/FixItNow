import uuid
import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, Float, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.category import ServiceCategory
    from app.db.models.booking_history import BookingStatusHistory
    from app.db.models.review import Review
    from app.db.models.booking_attempt import BookingMechanicAttempt

class BookingStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    BROADCASTING = "BROADCASTING"
    ACCEPTED = "ACCEPTED"
    EN_ROUTE = "EN_ROUTE"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED_BY_CUSTOMER = "CANCELLED_BY_CUSTOMER"
    CANCELLED_BY_MECHANIC = "CANCELLED_BY_MECHANIC"
    EXPIRED = "EXPIRED"

class Booking(Base, TimestampMixin):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("service_categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    customer_lat: Mapped[float] = mapped_column(Float, nullable=False)
    customer_lng: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_status_enum", values_callable=lambda x: [e.value for e in x]),
        default=BookingStatus.REQUESTED,
        nullable=False,
        index=True
    )
    accepted_mechanic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    price_estimate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    final_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    customer: Mapped["User"] = relationship(
        "User",
        foreign_keys=[customer_id],
        back_populates="customer_bookings",
        lazy="selectin"
    )
    category: Mapped["ServiceCategory"] = relationship(
        "ServiceCategory",
        back_populates="bookings",
        lazy="selectin"
    )
    accepted_mechanic: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[accepted_mechanic_id],
        back_populates="assigned_bookings",
        lazy="selectin"
    )
    status_history: Mapped[List["BookingStatusHistory"]] = relationship(
        "BookingStatusHistory",
        back_populates="booking",
        cascade="all, delete-orphan",
        order_by="BookingStatusHistory.changed_at.asc()",
        lazy="selectin"
    )
    review: Mapped[Optional["Review"]] = relationship(
        "Review",
        back_populates="booking",
        uselist=False,
        cascade="all, delete-orphan"
    )
    attempts: Mapped[List["BookingMechanicAttempt"]] = relationship(
        "BookingMechanicAttempt",
        back_populates="booking",
        cascade="all, delete-orphan"
    )

# Composite / Specific indexes as per requirement
Index("ix_bookings_created_at", Booking.created_at)
Index("ix_bookings_status_created", Booking.status, Booking.created_at)
