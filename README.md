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
python -m venv venv
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
| POST | `/createUser?name=...&email=...&plan_id=1` | Create a user |
| POST | `/updateUserByEmail?email=...&newName=...&newPlanName=...&newAccountStatus=...` | Update a user by email |
| GET | `/listUserAccounts` | List all users (no internal IDs in response) |
| POST | `/modifySubscriptionPlan?name=...&price=...&max_streams=...` | Update a subscription plan by name |
| POST | `/createSubscriptionPlan?name=...&price=...&max_streams=...` | Create a new subscription plan |
| GET | `/listSubscriptionPlans` | List all subscription plans |
| POST | `/createModifyPaymentInfo?email=...&amount=9.99&status=Success` | Record a payment by email |
| GET | `/reportMonthlyRevenue?month=3&year=2025` | Total revenue for a month |

### Device & Location

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/addDevice?email=...&name=...` | Add a device to the account (by email) |
| GET | `/listDevices?email=...` | List devices for the account (by email) |
| GET | `/listLocations?email=...` | List locations used by the account (from sessions) |
### Streaming

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/attemptStateSession?email=...&device_name=...&latitude=...&longitude=...&ip_address=...` | Validate and start a session (by email, device name, location, IP) |
| POST | `/attemptStartSession?email=...&latitude=...&longitude=...&ip_address=...` | Validate and start a session (by email, location, IP); returns whether access was granted |
| POST | `/trackUserLoginLogout?email=...&action=login` | Log login/logout to audit by email |
| POST | `/createModifyWatchTime?session_id=1&duration_seconds=3600` | Set session end time by duration |
| GET | `/listWatchHistory?email=...` | Watch history for the account (by email) |

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

# Create a user (plan_id must exist)
curl -X POST "http://localhost:8000/createUser?name=Jane&email=jane@example.com&plan_id=1"

# Update a user by email (plan name must exist)
curl -X POST "http://localhost:8000/updateUserByEmail?email=jane@example.com&newName=Jane&newPlanName=Basic&newAccountStatus=active"

# Modify a subscription plan by name
curl -X POST "http://localhost:8000/modifySubscriptionPlan?name=Basic&price=9.99&max_streams=2"

# List devices and watch history by email
curl "http://localhost:8000/listDevices?email=jane@example.com"
curl "http://localhost:8000/listWatchHistory?email=jane@example.com"

# Attempt session (email, device name, location, IP)
curl -X POST "http://localhost:8000/attemptStateSession?email=jane@example.com&device_name=iPhone&latitude=37.7&longitude=-122.4&ip_address=192.168.1.1"

# Track login/logout by email
curl -X POST "http://localhost:8000/trackUserLoginLogout?email=jane@example.com&action=login"

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
