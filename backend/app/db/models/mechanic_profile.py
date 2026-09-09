import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Float, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.category import ServiceCategory

class MechanicProfile(Base, TimestampMixin):
    __tablename__ = "mechanic_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    service_radius_km: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    current_lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rating_avg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    jobs_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="mechanic_profile")
    categories: Mapped[List["ServiceCategory"]] = relationship(
        "ServiceCategory",
        secondary="mechanic_service_categories",
        back_populates="mechanics",
        lazy="selectin"
    )
