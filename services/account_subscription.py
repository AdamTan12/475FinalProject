"""
Account & Subscription Management APIs.
updateUserByEmail, createUser, listUserAccounts, createModifySubscriptionPlan, listSubscriptionPlans,
createModifyPaymentInfoByEmail, reportMonthlyRevenue.
"""
from db.connection import get_connection


def createUser(name: str, email: str, plan_id: int):
    """
    Create Users
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (name, email, plan_id)
                VALUES (%s, %s, %s)
                """,
                (name, email, plan_id),
            )

def updateUserByEmail(email: str, newName: str, newPlanName: str, newAccountStatus: str):
    """
    Update user by email. Resolves plan by name internally.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT plan_id FROM subscription_plans WHERE name = %s",
                (newPlanName,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Plan not found: {newPlanName}")
            plan_id = row[0]
            cur.execute(
                """
                UPDATE users SET name = %s, plan_id = %s, account_status = %s, updated_at = NOW()
                WHERE email = %s
                """,
                (newName, plan_id, newAccountStatus, email),
            )


def listUserAccounts():
    """Select from Users. Returns list of user rows (no user_id in response)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT name, email, plan_id, home_location_id, account_status, created_at, updated_at
                FROM users
                ORDER BY email
                """
            )
            columns = [d[0] for d in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def modifySubscriptionPlan(name: str, price: float, max_streams: int):
    """
    Update subscription plan by name only.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE subscription_plans
                SET price = %s, max_streams = %s
                WHERE name = %s
                """,
                (price, max_streams, name),
            )

def createSubscriptionPlan(name: str, price: float, max_streams: int):
    """
    Insert or Update SubscriptionPlans. Use plan_id for update; pass None for insert.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO subscription_plans (name, price, max_streams)
                VALUES (%s, %s, %s)
                """,
                (name, price, max_streams),
            )



def listSubscriptionPlans():
    """Return all subscription plans (for UI and to identify plan when modifying)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT plan_id, name, price, max_streams
                FROM subscription_plans
                ORDER BY plan_id
                """
            )
            columns = [d[0] for d in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def createModifyPaymentInfoByEmail(email: str, amount: float, status: str = "Pending"):
    """Insert into Payments table. Resolves user by email."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"User not found: {email}")
            user_id = row[0]
            cur.execute(
                """
                INSERT INTO payments (user_id, amount, status)
                VALUES (%s, %s, %s)
                """,
                (user_id, amount, status),
            )


def reportMonthlyRevenue(month: int, year: int) -> float:
    """
    Sum Amount from Payments where status is 'Success' for the given month/year.
    Returns total revenue for that month.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COALESCE(SUM(amount), 0)::float AS total
                FROM payments
                WHERE status = 'Success'
                  AND EXTRACT(MONTH FROM payment_date) = %s
                  AND EXTRACT(YEAR FROM payment_date) = %s
                """,
                (month, year),
            )
            row = cur.fetchone()
            return row[0] if row else 0.0
