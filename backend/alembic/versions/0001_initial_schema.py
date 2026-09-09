"""initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-09 18:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types idempotently
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role_enum') THEN
                CREATE TYPE user_role_enum AS ENUM ('customer', 'mechanic', 'admin');
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'booking_status_enum') THEN
                CREATE TYPE booking_status_enum AS ENUM (
                    'REQUESTED', 'BROADCASTING', 'ACCEPTED', 'EN_ROUTE', 'IN_PROGRESS',
                    'COMPLETED', 'CANCELLED_BY_CUSTOMER', 'CANCELLED_BY_MECHANIC', 'EXPIRED'
                );
            END IF;
        END $$;
    """)

    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', postgresql.ENUM('customer', 'mechanic', 'admin', name='user_role_enum', create_type=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_phone'), 'users', ['phone'], unique=True)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)

    # 2. service_categories table
    op.create_table(
        'service_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_service_categories_name'), 'service_categories', ['name'], unique=True)

    # 3. mechanic_profiles table
    op.create_table(
        'mechanic_profiles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('service_radius_km', sa.Float(), nullable=False, server_default='10.0'),
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('current_lat', sa.Float(), nullable=True),
        sa.Column('current_lng', sa.Float(), nullable=True),
        sa.Column('rating_avg', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('jobs_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_mechanic_profiles_is_available'), 'mechanic_profiles', ['is_available'], unique=False)

    # 4. mechanic_service_categories table
    op.create_table(
        'mechanic_service_categories',
        sa.Column('mechanic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('mechanic_profiles.user_id', ondelete='CASCADE'), primary_key=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('service_categories.id', ondelete='CASCADE'), primary_key=True),
    )

    # 5. bookings table
    op.create_table(
        'bookings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('service_categories.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('customer_lat', sa.Float(), nullable=False),
        sa.Column('customer_lng', sa.Float(), nullable=False),
        sa.Column('status', postgresql.ENUM(
            'REQUESTED', 'BROADCASTING', 'ACCEPTED', 'EN_ROUTE', 'IN_PROGRESS',
            'COMPLETED', 'CANCELLED_BY_CUSTOMER', 'CANCELLED_BY_MECHANIC', 'EXPIRED',
            name='booking_status_enum',
            create_type=False
        ), nullable=False, server_default='REQUESTED'),
        sa.Column('accepted_mechanic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('price_estimate', sa.Float(), nullable=True),
        sa.Column('final_price', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_bookings_customer_id'), 'bookings', ['customer_id'], unique=False)
    op.create_index(op.f('ix_bookings_category_id'), 'bookings', ['category_id'], unique=False)
    op.create_index(op.f('ix_bookings_status'), 'bookings', ['status'], unique=False)
    op.create_index(op.f('ix_bookings_accepted_mechanic_id'), 'bookings', ['accepted_mechanic_id'], unique=False)
    op.create_index(op.f('ix_bookings_created_at'), 'bookings', ['created_at'], unique=False)
    op.create_index('ix_bookings_status_created', 'bookings', ['status', 'created_at'], unique=False)

    # 6. booking_status_history table
    op.create_table(
        'booking_status_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('booking_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('changed_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
    )
    op.create_index(op.f('ix_booking_status_history_booking_id'), 'booking_status_history', ['booking_id'], unique=False)
    op.create_index(op.f('ix_booking_status_history_changed_at'), 'booking_status_history', ['changed_at'], unique=False)

    # 7. reviews table
    op.create_table(
        'reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('booking_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('mechanic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='check_valid_rating'),
    )
    op.create_index(op.f('ix_reviews_booking_id'), 'reviews', ['booking_id'], unique=True)
    op.create_index(op.f('ix_reviews_customer_id'), 'reviews', ['customer_id'], unique=False)
    op.create_index(op.f('ix_reviews_mechanic_id'), 'reviews', ['mechanic_id'], unique=False)

    # 8. booking_mechanic_attempts table
    op.create_table(
        'booking_mechanic_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('booking_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('mechanic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('wave', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_booking_mechanic_attempts_booking_id'), 'booking_mechanic_attempts', ['booking_id'], unique=False)
    op.create_index(op.f('ix_booking_mechanic_attempts_mechanic_id'), 'booking_mechanic_attempts', ['mechanic_id'], unique=False)
    op.create_index('ix_attempt_booking_mechanic', 'booking_mechanic_attempts', ['booking_id', 'mechanic_id'], unique=False)


def downgrade() -> None:
    op.drop_table('booking_mechanic_attempts')
    op.drop_table('reviews')
    op.drop_table('booking_status_history')
    op.drop_table('bookings')
    op.drop_table('mechanic_service_categories')
    op.drop_table('mechanic_profiles')
    op.drop_table('service_categories')
    op.drop_table('users')
    op.execute('DROP TYPE IF EXISTS booking_status_enum')
    op.execute('DROP TYPE IF EXISTS user_role_enum')
