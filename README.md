# Video Stream Platform API

Backend API for a Netflix-style streaming platform (Python + PostgreSQL). Manages users, subscriptions, devices, locations, streaming sessions, and reporting.

**Team:** Powerpuff Boys — Joshua Lazarte, Chien Nguyen, Tom Strzyz, Adam Tan

---

## Prerequisites

- **Python 3.10+**
- **PostgreSQL** (running locally or remote)
- A database (e.g. `streaming_db`) created in PostgreSQL

---

## Setup

### 1. Clone and enter the project

```bash
cd 475FinalProject
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the database

Copy the example env file and set your PostgreSQL URL:

```bash
cp .env.example .env
```

Edit `.env` and set `DATABASE_URL` to your database:

```
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE_NAME
```

Example for a local database named `streaming_db`:

```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/streaming_db
```

### 5. Create the database schema

Run the schema SQL against your database so tables exist:

```bash
psql "$DATABASE_URL" -f db/schema.sql
```

Or from `psql`:

```bash
psql -U postgres -d streaming_db -f db/schema.sql
```

### 6. (Optional) Seed sample data

Populate the database with ~100 users, plans, locations, devices, payments, and sessions for testing:

```bash
python seed_sample_data.py
```

> **Note:** This clears all existing data before inserting. Re-running it resets the database to a clean sample state.

---

## Running the project

Start the API server from the project root:

```bash
python main.py
```

The server runs at **http://localhost:8000**.

- **Interactive API docs:** http://localhost:8000/docs  
- **ReDoc:** http://localhost:8000/redoc  

To run with uvicorn directly:

```bash
uvicorn api.routes:app --reload --host 0.0.0.0 --port 8000
```

---

## Using the API

All endpoints are under the base URL `http://localhost:8000`. Use query parameters for GET and form/JSON for POST as needed.

### Account & Subscription

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/createModifyUser?action=create&name=...&email=...&plan_id=1` | Create or update a user |
| GET | `/listUserAccounts` | List all users |
| POST | `/createModifySubscriptionPlan?plan_id=...&name=...&price=...&max_streams=...` | Create (plan_id empty) or update a plan |
| GET | `/listSubscriptionPlans` | List all subscription plans |
| POST | `/createModifyPaymentInfo?user_id=1&amount=9.99&status=Success` | Record a payment |
| GET | `/reportMonthlyRevenue?month=3&year=2025` | Total revenue for a month |

### Device & Location

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/listDevices?user_id=1` | List devices for a user |
| GET | `/listLocations?user_id=1` | List locations used by a user (from sessions) |
| POST | `/validateDeviceMFA?device_id=1&location_id=1&user_home_location_id=1` | Check if device/location requires MFA |

### Streaming

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/attemptStartSession?user_id=1&device_id=1&location_id=1` | Try to start a session (checks concurrency and 30-day rule) |
| POST | `/trackUserLoginLogout?user_id=1&action=login` | Log login/logout (stub) |
| POST | `/createModifyWatchTime?session_id=1&duration_seconds=3600` | Set session end time by duration |
| GET | `/listWatchHistory?user_id=1` | Watch history with locations and devices |

### Reporting

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reportTotalActiveSessions` | Count of active (open) sessions |
| GET | `/reportSuspiciousActivity` | Users with active sessions in more than 2 locations |

### Example requests (curl)

```bash
# List all users
curl "http://localhost:8000/listUserAccounts"

# List subscription plans
curl "http://localhost:8000/listSubscriptionPlans"

# Monthly revenue for March 2025
curl "http://localhost:8000/reportMonthlyRevenue?month=3&year=2025"

# Create a user (action=create, plan_id must exist)
curl -X POST "http://localhost:8000/createModifyUser?action=create&name=Jane&email=jane@example.com&plan_id=1"

# Try to start a streaming session
curl -X POST "http://localhost:8000/attemptStartSession?user_id=1&device_id=1&location_id=1"

# Total active sessions
curl "http://localhost:8000/reportTotalActiveSessions"
```

---

## Project structure

```
475FinalProject/
├── README.md
├── requirements.txt
├── .env.example
├── main.py                 # Run the server
├── seed_sample_data.py     # Populate DB with sample data
├── config/
│   └── settings.py         # DATABASE_URL from environment
├── db/
│   ├── connection.py      # get_connection() for PostgreSQL
│   └── schema.sql         # Table definitions
├── services/              # Business logic (API implementations)
│   ├── account_subscription.py
│   ├── device_location.py
│   ├── streaming.py
│   └── reporting.py
└── api/
    └── routes.py          # FastAPI routes → services
```

---

## Calling the API from Python

You can also use the service layer directly (no HTTP), for example in tests or scripts:

```python
from services.account_subscription import reportMonthlyRevenue, listUserAccounts

revenue = reportMonthlyRevenue(3, 2025)
users = listUserAccounts()
```

Run such code from the project root so that `config`, `db`, and `services` are on `PYTHONPATH`.
