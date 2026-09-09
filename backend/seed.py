import asyncio
import uuid
import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.db.models.user import User, UserRole
from app.db.models.mechanic_profile import MechanicProfile
from app.db.models.category import ServiceCategory
from app.core.security import get_password_hash
from app.core.logging import setup_logging, logger

setup_logging()

CATEGORIES = [
    {"name": "Fan Repair", "description": "Ceiling and table fan repair, capacitor replacement, rewinding"},
    {"name": "Mixer/Grinder Repair", "description": "Mixer jar coupler, motor blade, and wiring repair"},
    {"name": "Switchboard/Wiring", "description": "MCB, socket, switchboard, fuse replacement and home rewiring"},
    {"name": "AC Repair", "description": "Air conditioner cooling issues, gas refill, PCB repair and maintenance"},
    {"name": "Washing Machine", "description": "Motor, drum, drain pump, and motherboard repair"},
    {"name": "Other Electrical", "description": "General electrical appliances, iron, water heater, inverters"},
]

ADMIN_DATA = {
    "name": "Super Admin",
    "email": "admin@fixitnow.local",
    "phone": "+919900000001",
    "password": "Admin@123",
    "role": UserRole.ADMIN,
}

CUSTOMERS_DATA = [
    {"name": "Rahul Sharma", "email": "customer1@fixitnow.local", "phone": "+919800000001", "password": "Customer@123"},
    {"name": "Priya Patel", "email": "customer2@fixitnow.local", "phone": "+919800000002", "password": "Customer@123"},
    {"name": "Anil Verma", "email": "customer3@fixitnow.local", "phone": "+919800000003", "password": "Customer@123"},
]

# Mechanics centered around Pune demo cluster (Demo customer: Shivajinagar 18.5314, 73.8446)
MECHANICS_DATA = [
    {
        "name": "Ramesh Electrician (Near ~1.2km)",
        "email": "mechanic1@fixitnow.local",
        "phone": "+919700000001",
        "password": "Mechanic@123",
        "categories": ["Fan Repair", "Switchboard/Wiring", "AC Repair"],
        "lat": 18.5204,
        "lng": 73.8567,
        "radius_km": 10.0,
        "rating_avg": 4.9,
        "jobs_completed": 42,
    },
    {
        "name": "Suresh Tech (Near ~3.1km)",
        "email": "mechanic2@fixitnow.local",
        "phone": "+919700000002",
        "password": "Mechanic@123",
        "categories": ["Fan Repair", "Mixer/Grinder Repair", "Washing Machine"],
        "lat": 18.5590,
        "lng": 73.8260,
        "radius_km": 10.0,
        "rating_avg": 4.8,
        "jobs_completed": 28,
    },
    {
        "name": "Amit Services (Mid ~5.8km)",
        "email": "mechanic3@fixitnow.local",
        "phone": "+919700000003",
        "password": "Mechanic@123",
        "categories": ["Fan Repair", "Other Electrical", "AC Repair"],
        "lat": 18.5074,
        "lng": 73.8077,
        "radius_km": 10.0,
        "rating_avg": 4.6,
        "jobs_completed": 15,
    },
    {
        "name": "Pooja Electricals (Far in-radius ~8.2km)",
        "email": "mechanic4@fixitnow.local",
        "phone": "+919700000004",
        "password": "Mechanic@123",
        "categories": ["Fan Repair", "AC Repair", "Switchboard/Wiring"],
        "lat": 18.5980,
        "lng": 73.7990,
        "radius_km": 12.0,
        "rating_avg": 4.7,
        "jobs_completed": 19,
    },
    {
        "name": "Vikram Repairs (Outside-radius ~18.5km)",
        "email": "mechanic5@fixitnow.local",
        "phone": "+919700000005",
        "password": "Mechanic@123",
        "categories": ["Fan Repair", "Washing Machine", "Mixer/Grinder Repair"],
        "lat": 18.6298,
        "lng": 73.7997,
        "radius_km": 8.0,
        "rating_avg": 4.5,
        "jobs_completed": 9,
    },
]

async def seed_data():
    logger.info("Starting idempotent FixItNow database seeding...")
    async with AsyncSessionLocal() as db:
        # 1. Seed Categories
        category_map = {}
        for cat_data in CATEGORIES:
            stmt = select(ServiceCategory).where(ServiceCategory.name == cat_data["name"])
            res = await db.execute(stmt)
            cat = res.scalar_one_or_none()
            if not cat:
                cat = ServiceCategory(name=cat_data["name"], description=cat_data["description"])
                db.add(cat)
                await db.flush()
                logger.info(f"Seeded category: {cat.name}")
            category_map[cat.name] = cat

        # 2. Seed Admin
        stmt = select(User).where(User.email == ADMIN_DATA["email"])
        res = await db.execute(stmt)
        admin = res.scalar_one_or_none()
        if not admin:
            admin = User(
                name=ADMIN_DATA["name"],
                email=ADMIN_DATA["email"],
                phone=ADMIN_DATA["phone"],
                password_hash=get_password_hash(ADMIN_DATA["password"]),
                role=ADMIN_DATA["role"],
            )
            db.add(admin)
            logger.info(f"Seeded admin: {admin.email}")

        # 3. Seed Customers
        for c_data in CUSTOMERS_DATA:
            stmt = select(User).where(User.email == c_data["email"])
            res = await db.execute(stmt)
            customer = res.scalar_one_or_none()
            if not customer:
                customer = User(
                    name=c_data["name"],
                    email=c_data["email"],
                    phone=c_data["phone"],
                    password_hash=get_password_hash(c_data["password"]),
                    role=UserRole.CUSTOMER,
                )
                db.add(customer)
                logger.info(f"Seeded customer: {customer.email}")

        # 4. Seed Mechanics
        for m_data in MECHANICS_DATA:
            stmt = select(User).where(User.email == m_data["email"]).options(
                selectinload(User.mechanic_profile).selectinload(MechanicProfile.categories)
            )
            res = await db.execute(stmt)
            user = res.scalar_one_or_none()

            if not user:
                user = User(
                    name=m_data["name"],
                    email=m_data["email"],
                    phone=m_data["phone"],
                    password_hash=get_password_hash(m_data["password"]),
                    role=UserRole.MECHANIC,
                )
                db.add(user)
                await db.flush()

                profile = MechanicProfile(
                    user_id=user.id,
                    service_radius_km=m_data["radius_km"],
                    is_available=True,
                    current_lat=m_data["lat"],
                    current_lng=m_data["lng"],
                    rating_avg=m_data["rating_avg"],
                    jobs_completed=m_data["jobs_completed"],
                    verified=True,
                )
                profile.categories = [category_map[cat_name] for cat_name in m_data["categories"] if cat_name in category_map]
                db.add(profile)
                logger.info(f"Seeded mechanic: {user.email} with {len(profile.categories)} categories")

        await db.commit()
        logger.info("Database seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
