# FixItNow — Production-Grade On-Demand Appliance Repair Marketplace

FixItNow is a two-sided marketplace connecting customers needing electrical and appliance repairs with qualified nearby technicians/mechanics. It features real-time Haversine geographic matching, multi-wave broadcasting, strict state machine transitions, PostgreSQL concurrency-safe job acceptance (`FOR UPDATE`), native WebSocket channels, and an intuitive React + Vite frontend.

---

## 🚀 Architecture Overview

```text
Browser (React + Vite :5173)
   ↕  (REST API + Native WebSockets)
FastAPI Backend (:8000)
   ↕  (SQLAlchemy 2.0 Async + asyncpg + Alembic)
PostgreSQL 16 (:5432)
```

### Key Engineering Pillars
1. **State Machine Integrity**: Centralized `transition_booking` preventing invalid transitions and keeping an immutable `booking_status_history` audit trail.
2. **Haversine Distance Engine**: Real spherical trigonometric distance calculations (`EARTH_RADIUS_KM = 6371`) with dynamic wave dispatch (Wave 1: top 5 nearest mechanics, Wave 2: second-wave remaining mechanics, Expiry timeout).
3. **Concurrency-Safe Acceptance**: PostgreSQL `SELECT ... FOR UPDATE` row locking prevents double-booking when two mechanics accept simultaneously; losing mechanics receive HTTP `409 Conflict`.
4. **Native WebSocket Streaming**: Real-time two-way channels for customer status timelines (`/ws/customer/{booking_id}`) and mechanic job alerts (`/ws/mechanic/{mechanic_id}`).
5. **Idempotent Migrations & Seeding**: Auto-executing Alembic migrations and database seed script on startup.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy 2.0 (Async), asyncpg, Alembic, Pydantic v2, pydantic-settings, PyJWT, Passlib (bcrypt)
- **Database**: PostgreSQL 16 (in Docker)
- **Frontend**: React 18, Vite, Tailwind CSS, React Router v6, Axios, Lucide Icons, Native WebSocket API
- **Testing**: pytest, pytest-asyncio, httpx
- **Orchestration**: Docker & Docker Compose

---

## ⚡ Quick Start

### 1. Prerequisites
- Docker & Docker Compose installed.

### 2. Clone and Setup Environment
```bash
git clone https://github.com/Frpratik/FixItNow.git
cd FixItNow
cp .env.example .env
```

### 3. Launch with Docker Compose
```bash
docker compose up --build
```
*The API container automatically waits for PostgreSQL readiness, applies Alembic migrations, runs the seed script, and launches FastAPI.*

---

## 🌐 Application URLs

| Service | URL | Description |
| :--- | :--- | :--- |
| **Frontend Web App** | [http://localhost:5173](http://localhost:5173) | Customer, Mechanic, and Admin Portals |
| **Backend REST API** | [http://localhost:8000](http://localhost:8000) | FastAPI server |
| **Swagger Interactive Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | OpenAPI documentation |
| **ReDoc Specification** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Clean API documentation |
| **API Health Check** | [http://localhost:8000/health](http://localhost:8000/health) | System and Database health check |

---

## 🔑 Demo Seed Accounts

All passwords follow standard conventions and are pre-seeded into PostgreSQL:

| Role | Name | Email | Password | Details |
| :--- | :--- | :--- | :--- | :--- |
| **Admin** | Super Admin | `admin@fixitnow.local` | `Admin@123` | System oversight & force-resolve |
| **Customer 1** | Rahul Sharma | `customer1@fixitnow.local` | `Customer@123` | Pune Shivajinagar `(18.5314, 73.8446)` |
| **Customer 2** | Priya Patel | `customer2@fixitnow.local` | `Customer@123` | Secondary customer |
| **Customer 3** | Anil Verma | `customer3@fixitnow.local` | `Customer@123` | Tertiary customer |
| **Mechanic 1** | Ramesh Electrician | `mechanic1@fixitnow.local` | `Mechanic@123` | **1.2 km away** (Fan, Switchboard, AC) |
| **Mechanic 2** | Suresh Tech | `mechanic2@fixitnow.local` | `Mechanic@123` | **3.1 km away** (Fan, Mixer, Washing Machine) |
| **Mechanic 3** | Amit Services | `mechanic3@fixitnow.local` | `Mechanic@123` | **5.8 km away** (Fan, Other, AC) |
| **Mechanic 4** | Pooja Electricals | `mechanic4@fixitnow.local` | `Mechanic@123` | **8.2 km away** (Fan, AC, Switchboard) |
| **Mechanic 5** | Vikram Repairs | `mechanic5@fixitnow.local` | `Mechanic@123` | **18.5 km away** (Outside standard 10 km radius) |

*Tip: The login page contains **One-Click Quick Login** buttons for instant demo testing!*

---

## 🎬 End-to-End Demo Scenario

Open **two browser windows** side by side:

### Browser 1: Customer Workflow
1. Navigate to [http://localhost:5173/login](http://localhost:5173/login) and click **Customer** quick login (`customer1@fixitnow.local`).
2. Click **Book New Repair**.
3. Select **Fan Repair**, enter description *"Ceiling fan makes humming noise and does not rotate"*, click **⚡ Pune Demo Pin** to populate demo coordinates `(18.5314, 73.8446)`, and submit.
4. You are redirected to `/bookings/{id}` where status shows **BROADCASTING (Searching Mechanics...)** with a live WebSocket indicator.

### Browser 2: Mechanic Workflow
1. Navigate to [http://localhost:5173/login](http://localhost:5173/login) in an Incognito window and click **Mechanic 1** (`mechanic1@fixitnow.local`).
2. Notice the live **Incoming Nearby Requests** radar displaying the Fan Repair alert with **📍 1.2 km away**.
3. Click **Accept Job**.

### Real-Time Synchronization
1. In Browser 1 (Customer), the status instantly updates to **ACCEPTED** via WebSocket with Ramesh Electrician's name, phone, and rating.
2. In Browser 2 (Mechanic), click **Start Journey (EN_ROUTE)**. Customer screen immediately updates to **EN_ROUTE**.
3. In Browser 2, click **Arrived & Start Work (IN_PROGRESS)**. Customer screen updates to **IN_PROGRESS**.
4. In Browser 2, click **Mark Job as Completed**. Customer screen updates to **COMPLETED**.
5. In Browser 1 (Customer), click **Leave Review**, select **5 Stars**, write a comment, and submit.
6. The mechanic's rating average and completed job counter update instantly!

---

## 📐 Matching & Timeout Engine Details

- **Wave 1 Broadcast**: When a booking is created, the system calculates the Haversine distance between customer coordinates and all online, category-qualified mechanics. The nearest 5 mechanics within `MAX_RADIUS_KM` (10 km) receive instant WebSocket job notifications.
- **Wave 2 Second-Wave Broadcast**: If no mechanic accepts within `FIRST_WAVE_TIMEOUT_SEC` (default 60s), the background `BookingMonitor` automatically dispatches the job to the remaining qualified mechanics within radius.
- **Expiry Timeout**: If no mechanic accepts within `EXPIRY_TIMEOUT_MIN` (default 5 mins), the booking automatically transitions `BROADCASTING → EXPIRED`, notifying the customer.
- **Mechanic Cancellation & Re-broadcasting**: If an assigned mechanic cancels (`CANCELLED_BY_MECHANIC`), the booking resets to `BROADCASTING` and automatically re-broadcasts to other available mechanics.

---

## 🔒 Concurrency Race Condition Safety

When two mechanics click Accept simultaneously:
```sql
BEGIN;
SELECT * FROM bookings WHERE id = :booking_id FOR UPDATE;
-- Verify status is BROADCASTING and accepted_mechanic_id IS NULL
UPDATE bookings SET status = 'ACCEPTED', accepted_mechanic_id = :mechanic_id WHERE id = :booking_id;
COMMIT;
```
The first mechanic's transaction succeeds. The second mechanic's transaction reads the locked row after commit, detects that `status != BROADCASTING`, and receives HTTP `409 Conflict` with the structured payload:
```json
{
  "error": {
    "code": "CONFLICT",
    "message": "Booking has already been accepted by another mechanic or is no longer available.",
    "details": {
      "current_status": "ACCEPTED"
    }
  }
}
```

---

## 🧪 Running Automated Tests

Run the full pytest suite inside the backend container or locally:

```bash
cd backend
pytest tests/ -v
```

Tests include:
- `test_auth.py`: Registration, duplicate checks, login, refresh, role guards.
- `test_distance.py`: Spherical Haversine distance calculations.
- `test_state_machine.py`: Legal progressions, cancellation, and rejection of illegal state changes.
- `test_matching.py`: Category filtering, radius filtering, online status filtering.
- `test_concurrency_race.py`: **True concurrent async race test** verifying 1 winner (200) and 1 loser (409).
- `test_reviews.py`: Review constraints, ratings 1-5, completed status validation.
- `test_admin.py`: Force-resolve administrative overrides and role protection.

---

## 📂 Project Structure

```text
FixItNow/
├── docker-compose.yml
├── .env.example
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── seed.py
│   ├── alembic/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/         # config, security, logging, exceptions
│   │   ├── db/           # base, session, models (User, Profile, Booking, History, Review, Attempt)
│   │   ├── schemas/      # Pydantic v2 schemas
│   │   ├── api/          # deps, auth, bookings, mechanic, admin, health, websockets
│   │   ├── services/     # state machine, matching, booking, reviews, auth
│   │   ├── websocket/    # connection manager
│   │   └── background/   # async booking monitor loop
│   └── tests/            # pytest suite
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── api/          # axios client, websocket client
        ├── context/      # auth context
        ├── components/   # navbar, badges, timeline, review modal
        └── pages/        # Login, Register, Customer, BookingDetails, Mechanic, Admin
```
