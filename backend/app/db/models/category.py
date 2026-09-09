import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db.base import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

if TYPE_CHECKING:
    from app.db.models.mechanic_profile import MechanicProfile
    from app.db.models.booking import Booking

mechanic_service_categories = Table(
    "mechanic_service_categories",
    Base.metadata,
    Column("mechanic_id", PG_UUID(as_uuid=True), ForeignKey("mechanic_profiles.user_id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", PG_UUID(as_uuid=True), ForeignKey("service_categories.id", ondelete="CASCADE"), primary_key=True),
)

class ServiceCategory(Base):
    __tablename__ = "service_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    # Relationships
    mechanics: Mapped[List["MechanicProfile"]] = relationship(
        "MechanicProfile",
        secondary=mechanic_service_categories,
        back_populates="categories"
    )
    bookings: Mapped[List["Booking"]] = relationship(
        "Booking",
        back_populates="category"
    )
