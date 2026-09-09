import uuid
import enum
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.mechanic_profile import MechanicProfile
    from app.db.models.booking import Booking
    from app.db.models.review import Review

class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    MECHANIC = "mechanic"
    ADMIN = "admin"

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )

    # Relationships
    mechanic_profile: Mapped[Optional["MechanicProfile"]] = relationship(
        "MechanicProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    customer_bookings: Mapped[List["Booking"]] = relationship(
        "Booking",
        back_populates="customer",
        foreign_keys="[Booking.customer_id]"
    )
    assigned_bookings: Mapped[List["Booking"]] = relationship(
        "Booking",
        back_populates="accepted_mechanic",
        foreign_keys="[Booking.accepted_mechanic_id]"
    )
    reviews_given: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="customer",
        foreign_keys="[Review.customer_id]"
    )
    reviews_received: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="mechanic",
        foreign_keys="[Review.mechanic_id]"
    )
