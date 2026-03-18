# Video Stream Platform

Backend for a Netflix-style streaming platform (Python + PostgreSQL). Manages users, subscriptions, devices, locations, streaming sessions, and reporting.

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

Edit `.env` and set your PostgreSQL URL:

```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/streaming_db
```

### 5. Create the database schema

Run the schema SQL against your database:

```bash
psql -U postgres -d streaming_db -f db/schema.sql
```

### 6. Seed sample data

Populate the database with 4 plans, 100 users, ~254 devices, and ~1237 sessions:

```bash
python seed_sample_data.py
```

> **Note:** This clears all existing data before inserting. Re-running resets the database to a clean sample state.

---

## Running the command-line driver

The primary way to interact with the platform is through the command-line driver:

```bash
python driver.py
```

A numbered menu appears. Type a number and hit Enter to select an API. The driver prompts for any required input and prints the result.

### Available APIs in the driver

| # | API | Input Required |
|---|-----|----------------|
| 1 | `listSubscriptionPlans` | None |
| 2 | `listUserAccounts` | None |
| 3 | `listDevices` | email |
| 4 | `listLocationsByEmail` | email |
| 5 | `attemptStartSession` | email, device fingerprint, latitude, longitude |
| 6 | `attemptEndSession` | email, device fingerprint |
| 7 | `reportTotalActiveSessions` | None |
| 8 | `reportSuspiciousActivity` | None — flags users exceeding their plan's max_streams |

---

## Demo test flows

### Test data (after seeding)

| Item | Value |
|------|-------|
| Basic plan user (max 1 stream, active) | `sampleuser7@example.com` |
| Inactive user | `sampleuser5@example.com` |
| sampleuser7 trusted device fingerprint | `seed-device-16` |
| sampleuser7 other devices | `seed-device-17`, `seed-device-18` |
| Valid location lat/lon | `25.5752500` / `-109.8733900` |
| Invalid location (not in DB) | `99.9999` / `99.9999` |

### Test 1 — Session granted
```
Select: 5
email:       sampleuser7@example.com
fingerprint: seed-device-16
lat:         25.5752500
lon:         -109.8733900
```
Expected: `GRANTED`

### Test 2 — Prove session was counted
```
Select: 7
```
Expected: active session count increased

### Test 3 — Stream limit enforced
Run `attemptStartSession` again with the same user, different device:
```
Select: 5
email:       sampleuser7@example.com
fingerprint: seed-device-17
lat:         25.5752500
lon:         -109.8733900
```
Expected: `DENIED: Stream limit reached (1/1 active sessions)`

### Test 4 — End the session
```
Select: 6
email:       sampleuser7@example.com
fingerprint: seed-device-16
```
Expected: `Session ended.`

### Test 5 — Prove session ended
```
Select: 7
```
Expected: count went back down

### Test 6 — Inactive account blocked
```
Select: 5
email:       sampleuser5@example.com
fingerprint: seed-device-1
lat:         25.5752500
lon:         -109.8733900
```
Expected: `DENIED: Account is not active.`

### Test 7 — Unknown location blocked
```
Select: 5
email:       sampleuser7@example.com
fingerprint: seed-device-16
lat:         99.9999
lon:         99.9999
```
Expected: `DENIED: This location is not in the database.`

### Test 8 — Suspicious activity report
```
Select: 8
```
Expected: list of users with more than 2 active sessions

---

## Running the HTTP server (optional)

```bash
python main.py
```

Server runs at **http://localhost:8000**.
Interactive docs at **http://localhost:8000/docs**

---

## Running tests

```bash
python -m pytest tests/ -v
# or
python tests/test_runner.py
```

---

## Project structure

```
475FinalProject/
├── README.md
├── requirements.txt
├── main.py                 # FastAPI HTTP server (optional)
├── driver.py               # Command-line driver (primary interface)
├── seed_sample_data.py     # Populate DB with sample data
├── config/
│   └── settings.py         # DATABASE_URL from .env
├── db/
│   ├── connection.py       # get_connection() context manager
│   └── schema.sql          # Table definitions
├── services/               # Business logic
│   ├── account_subscription.py
│   ├── device_location.py
│   ├── streaming.py
│   └── reporting.py
├── api/
│   └── routes.py           # FastAPI routes → services
└── tests/
    ├── test_account_subscription.py
    ├── test_device_location.py
    ├── test_streaming_reporting.py
    └── test_runner.py
```

---

## Schema

6 tables: `subscription_plan`, `account_status`, `location`, `user`, `device`, `session`

See `db/schema.sql` for full definitions.

---

## Notes

- **Device fingerprinting** — `device_fingerprint` is a caller-supplied string. For testing, seeded devices use the pattern `seed-device-<N>`. In production, fingerprint generation would be handled by a native SDK.
- **Approved locations** — The `location` table acts as a whitelist. Locations must be added via `addLocation` before sessions can be started there.
- **Stream enforcement** — `attemptStartSession` enforces: account must be active, device must be registered, location must exist in DB, active session count must not exceed plan's `max_streams`.
- **Suspicious activity** — `reportSuspiciousActivity` flags users whose active session count exceeds their plan's `max_streams`. A Basic user (max 1) with 2 active sessions is flagged; a Family user (max 6) with 3 is not.
