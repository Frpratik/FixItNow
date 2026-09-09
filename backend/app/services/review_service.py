import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.models.booking import Booking, BookingStatus
from app.db.models.review import Review
from app.db.models.mechanic_profile import MechanicProfile
from app.schemas.review import ReviewCreateRequest, ReviewResponse
from app.core.exceptions import AppException, ForbiddenError, ConflictError, NotFoundError
from app.core.logging import logger

class ReviewService:
    @staticmethod
    async def create_review(
        db: AsyncSession,
        booking_id: uuid.UUID,
        customer_id: uuid.UUID,
        req: ReviewCreateRequest
    ) -> ReviewResponse:
        # Load booking
        stmt = select(Booking).where(Booking.id == booking_id).options(
            selectinload(Booking.review)
        )
        result = await db.execute(stmt)
        booking = result.scalar_one_or_none()

        if not booking:
            raise NotFoundError("Booking not found.")

        # Customer ownership check
        if booking.customer_id != customer_id:
            raise ForbiddenError("You can only review your own bookings.")

        # Booking status check
        if booking.status != BookingStatus.COMPLETED:
            raise ConflictError(f"Reviews can only be submitted for COMPLETED bookings (current status: {booking.status.value}).")

        # Must have accepted mechanic
        if not booking.accepted_mechanic_id:
            raise ConflictError("Cannot review a booking without an assigned mechanic.")

        # Check existing review
        if booking.review:
            raise ConflictError("A review has already been submitted for this booking.")

        # Create review
        review = Review(
            booking_id=booking.id,
            customer_id=customer_id,
            mechanic_id=booking.accepted_mechanic_id,
            rating=req.rating,
            comment=req.comment.strip() if req.comment else None
        )
        db.add(review)
        await db.flush()

        # Update mechanic stats
        prof_stmt = select(MechanicProfile).where(MechanicProfile.user_id == booking.accepted_mechanic_id)
        prof_res = await db.execute(prof_stmt)
        profile = prof_res.scalar_one_or_none()

        if profile:
            # Recalculate average rating & jobs completed
            ratings_stmt = select(
                func.avg(Review.rating).label("avg_rating"),
                func.count(Review.id).label("total_reviews")
            ).where(Review.mechanic_id == booking.accepted_mechanic_id)
            ratings_res = await db.execute(ratings_stmt)
            row = ratings_res.first()

            if row and row.avg_rating is not None:
                profile.rating_avg = round(float(row.avg_rating), 2)
            profile.jobs_completed += 1

        await db.commit()
        await db.refresh(review)

        logger.info(
            f"Review created for booking {booking.id} by customer {customer_id} (rating: {req.rating})",
            extra={
                "booking_id": booking.id,
                "user_id": customer_id,
                "mechanic_id": booking.accepted_mechanic_id,
                "event": "review_created",
                "extra_data": {"rating": req.rating}
            }
        )

        return ReviewResponse.model_validate(review)
