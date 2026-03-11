"""
Account & Subscription Management APIs.
modifyUser, createUser, listUserAccounts, createModifySubscriptionPlan, listSubscriptionPlans,
modifyUser, createUser, listUserAccounts, createSubscriptionPlan, modifySubscriptionPlan, listSubscriptionPlans.
"""
from db.connection import get_connection


def createUser(name: str, email: str, plan_id: int, status_id: int):
    """
    Create Users
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (name, email, plan_id, status_id)
                VALUES (%s, %s, %s, %s)
                """,
                (name, email, plan_id, status_id),
            )

def modifyUser(name: str, email: str, plan_id: int, status_id: int, user_id=None):
    """
    Modify Users and identify by email
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            if user_id is not None:
                cur.execute(
                    """
                    UPDATE users SET name = %s, plan_id = %s, status_id = %s, updated_at = NOW()
                    WHERE user_id = %s
                    """,
                    (name, plan_id, status_id, user_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE users SET name = %s, plan_id = %s, status_id = %s, updated_at = NOW()
                    WHERE email = %s
                    """,
                    (name, plan_id, status_id, email),
                )


def listUserAccounts():
    """Select from Users. Returns list of user rows."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id, name, email, plan_id, status_id, home_location_id, created_at, updated_at
                FROM users
                ORDER BY user_id
                """
            )
            columns = [d[0] for d in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def modifySubscriptionPlan(plan_id: int, name: str, price: float, max_streams: int):
    """
    Insert or Update SubscriptionPlans. Use plan_id for update; pass None for insert.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE subscription_plans
                SET name = %s, price = %s, max_streams = %s
                WHERE plan_id = %s
                """,
                (name, price, max_streams, plan_id),
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


