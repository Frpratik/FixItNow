#!/bin/sh
set -e

echo "Waiting for PostgreSQL database to become available..."
python -c "
import asyncio
import asyncpg
import os
import sys

async def check():
    db_url = os.environ.get('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@db:5432/fixitnow')
    # convert asyncpg url
    url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
    for _ in range(30):
        try:
            conn = await asyncpg.connect(url)
            await conn.close()
            print('PostgreSQL is ready!')
            sys.exit(0)
        except Exception as e:
            print(f'Waiting for db... {e}')
            await asyncio.sleep(2)
    sys.exit(1)

asyncio.run(check())
"

echo "Applying Alembic database migrations..."
alembic upgrade head

echo "Running initial database seeding..."
python seed.py

echo "Starting FixItNow FastAPI application server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
