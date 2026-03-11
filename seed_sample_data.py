"""
Seed the database with sample data: ~100 users, plans, locations, devices, payments, sessions.
Run from project root: python seed_sample_data.py
Re-runnable: clears existing data then inserts.
"""
import random
from datetime import datetime, timedelta
from db.connection import get_connection

# Fixed seed for reproducible data
random.seed(42)

PLANS = [
    ("Basic", 9.99, 1),
    ("Standard", 14.99, 2),
    ("Premium", 19.99, 4),
    ("Family", 24.99, 6),
]

LOCATION_DESCRIPTIONS = [
    "Seattle Home", "NYC Cafe", "Austin Office", "LA Apartment", "Chicago Home",
    "Denver Office", "Portland Home", "SF Coffee Shop", "Boston Library",
    "Miami Beach", "Phoenix Home", "Atlanta Office", "Dallas Home", "Minneapolis Cafe",
    "Detroit Home", "Philadelphia Office", "Houston Home", "San Diego Cafe",
    "Las Vegas Hotel", "DC Office", "Seattle Office", "NYC Home", "Austin Home",
    "LA Home", "Chicago Cafe", "Denver Home", "Portland Cafe", "SF Home",
    "Boston Home", "Miami Home", "Phoenix Office", "Atlanta Home", "Dallas Office",
    "Minneapolis Home", "Detroit Office", "Philadelphia Home", "Houston Office",
    "San Diego Home", "DC Home", "Seattle Cafe", "NYC Office", "Austin Cafe",
    "LA Office", "Chicago Office", "Denver Cafe", "Portland Office", "SF Office",
    "Boston Office", "Miami Office",
]

DEVICE_NAMES = ["iPhone", "Android", "Chrome", "Safari", "TV", "iPad", "Fire TV", "Roku"]

ACCOUNT_STATUSES = ["active", "inactive", "suspended"]


def main():
    with get_connection() as conn:
        cur = conn.cursor()

        # --- Clear existing data (FK-safe order) ---
        cur.execute("DELETE FROM sessions;")
        cur.execute("DELETE FROM payments;")
        cur.execute("DELETE FROM devices;")
        cur.execute("DELETE FROM users;")
        cur.execute("DELETE FROM locations;")
        cur.execute("DELETE FROM subscription_plans;")
        cur.execute("DELETE FROM account_statuses;")

        # Reset sequences so IDs start at 1
        cur.execute("ALTER SEQUENCE subscription_plans_plan_id_seq RESTART WITH 1;")
        cur.execute("ALTER SEQUENCE account_statuses_status_id_seq RESTART WITH 1;")
        cur.execute("ALTER SEQUENCE locations_location_id_seq RESTART WITH 1;")
        cur.execute("ALTER SEQUENCE users_user_id_seq RESTART WITH 1;")
        cur.execute("ALTER SEQUENCE devices_device_id_seq RESTART WITH 1;")
        cur.execute("ALTER SEQUENCE payments_payment_id_seq RESTART WITH 1;")
        cur.execute("ALTER SEQUENCE sessions_session_id_seq RESTART WITH 1;")

        # --- Insert account_statuses ---
        for status_name in ACCOUNT_STATUSES:
            cur.execute(
                "INSERT INTO account_statuses (status_name) VALUES (%s);",
                (status_name,),
            )
        num_statuses = len(ACCOUNT_STATUSES)

        # --- Insert subscription_plans ---
        for name, price, max_streams in PLANS:
            cur.execute(
                "INSERT INTO subscription_plans (name, price, max_streams) VALUES (%s, %s, %s);",
                (name, price, max_streams),
            )
        num_plans = len(PLANS)

        # --- Insert locations ---
        num_locations = len(LOCATION_DESCRIPTIONS)
        for desc in LOCATION_DESCRIPTIONS:
            lat = round(random.uniform(25.0, 48.0), 5) if random.random() > 0.3 else None
            lon = round(random.uniform(-125.0, -70.0), 5) if lat is not None else None
            cur.execute(
                "INSERT INTO locations (latitude, longitude, description) VALUES (%s, %s, %s);",
                (lat, lon, desc),
            )

        # --- Insert users (100) ---
        num_users = 100
        for i in range(1, num_users + 1):
            name = "Sample User %d" % i
            email = "sampleuser%d@example.com" % i
            plan_id = random.randint(1, num_plans)
            status_id = random.randint(1, num_statuses)
            home_location_id = random.randint(1, num_locations) if random.random() > 0.1 else None
            cur.execute(
                "INSERT INTO users (name, email, plan_id, status_id, home_location_id) VALUES (%s, %s, %s, %s, %s);",
                (name, email, plan_id, status_id, home_location_id),
            )

        # --- Insert devices (~2-3 per user) ---
        device_rows = []  # (user_id, name, is_trusted, last_seen_at_home)
        for user_id in range(1, num_users + 1):
            n_devices = random.randint(2, 3)
            names_used = random.sample(DEVICE_NAMES, min(n_devices, len(DEVICE_NAMES)))
            if n_devices > len(names_used):
                names_used += random.choices(DEVICE_NAMES, k=n_devices - len(names_used))
            for j, dname in enumerate(names_used[:n_devices]):
                is_trusted = j == 0
                last_seen = (datetime.utcnow() - timedelta(days=random.randint(0, 60))) if random.random() > 0.4 else None
                device_rows.append((user_id, dname, is_trusted, last_seen))
        for user_id, dname, is_trusted, last_seen in device_rows:
            cur.execute(
                "INSERT INTO devices (user_id, name, is_trusted, last_seen_at_home) VALUES (%s, %s, %s, %s);",
                (user_id, dname, is_trusted, last_seen),
            )
        num_devices = len(device_rows)

        # Build user_id -> list of device_ids (1-based device_id after insert order)
        cur.execute("SELECT device_id, user_id FROM devices ORDER BY device_id;")
        device_user = cur.fetchall()
        user_device_ids = {}
        for dev_id, uid in device_user:
            user_device_ids.setdefault(uid, []).append(dev_id)

        # --- Insert payments (~3-8 per user, spread over 6-12 months) ---
        cur.execute("SELECT user_id, plan_id FROM users;")
        user_plans = {uid: pid for uid, pid in cur.fetchall()}
        cur.execute("SELECT plan_id, price FROM subscription_plans;")
        plan_prices = {pid: float(price) for pid, price in cur.fetchall()}
        num_payments = 0
        base_date = datetime.utcnow() - timedelta(days=365)
        for user_id in range(1, num_users + 1):
            price = plan_prices[user_plans[user_id]]
            n_payments = random.randint(3, 8)
            for _ in range(n_payments):
                pay_date = base_date + timedelta(days=random.randint(0, 365))
                status = "Success" if random.random() > 0.15 else "Pending"
                cur.execute(
                    "INSERT INTO payments (user_id, amount, status, payment_date) VALUES (%s, %s, %s, %s);",
                    (user_id, price, status, pay_date),
                )
                num_payments += 1

        # --- Insert sessions (~5-20 per user, some active) ---
        num_sessions = 0
        session_base = datetime.utcnow() - timedelta(days=180)
        for user_id in range(1, num_users + 1):
            dev_ids = user_device_ids.get(user_id, [])
            if not dev_ids:
                continue
            loc_ids = list(range(1, num_locations + 1))
            n_sessions = random.randint(5, 20)
            for _ in range(n_sessions):
                start_time = session_base + timedelta(days=random.randint(0, 180), hours=random.randint(0, 23))
                # ~10% of sessions active (end_time NULL)
                if random.random() < 0.1:
                    end_time = None
                else:
                    end_time = start_time + timedelta(minutes=random.randint(15, 180))
                device_id = random.choice(dev_ids)
                location_id = random.choice(loc_ids)
                cur.execute(
                    "INSERT INTO sessions (user_id, device_id, location_id, start_time, end_time) VALUES (%s, %s, %s, %s, %s);",
                    (user_id, device_id, location_id, start_time, end_time),
                )
                num_sessions += 1

    print(
        "Inserted %d plans, %d locations, %d users, %d devices, %d payments, %d sessions."
        % (num_plans, num_locations, num_users, num_devices, num_payments, num_sessions)
    )
    print("Done.")


if __name__ == "__main__":
    main()
