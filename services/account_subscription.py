"""
Account & Subscription Management APIs.
createModifyUser, listUserAccounts, createModifySubscriptionPlan, listSubscriptionPlans,
createModifyPaymentInfo, reportMonthlyRevenue.
"""
from db.connection import get_connection


def createModifyUser(action: str, name: str, email: str, plan_id: int, **kwargs):
    """
    Insert or Update Users. action is 'create' or 'update'.
    For update, identify by email (or pass user_id in kwargs).
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            if action == "create":
                cur.execute(
                    """
                    INSERT INTO users (name, email, plan_id)
                    VALUES (%s, %s, %s)
                    """,
                    (name, email, plan_id),
                )
            elif action == "update":
                user_id = kwargs.get("user_id")
                if user_id is not None:
                    cur.execute(
                        """
                        UPDATE users SET name = %s, plan_id = %s, updated_at = NOW()
                        WHERE user_id = %s
                        """,
                        (name, plan_id, user_id),
                    )
                else:
                    cur.execute(
                        """
                        UPDATE users SET name = %s, plan_id = %s, updated_at = NOW()
                        WHERE email = %s
                        """,
                        (name, plan_id, email),
                    )
            else:
                raise ValueError("action must be 'create' or 'update'")


def listUserAccounts():
    """Select from Users. Returns list of user rows."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id, name, email, plan_id, home_location_id, account_status, created_at, updated_at
                FROM users
                ORDER BY user_id
                """
            )
            columns = [d[0] for d in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def createModifySubscriptionPlan(plan_id: int | None, name: str, price: float, max_streams: int):
    """
    Insert or Update SubscriptionPlans. Use plan_id for update; pass None for insert.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            if plan_id is None:
                cur.execute(
                    """
                    INSERT INTO subscription_plans (name, price, max_streams)
                    VALUES (%s, %s, %s)
                    """,
                    (name, price, max_streams),
                )
            else:
                cur.execute(
                    """
                    UPDATE subscription_plans
                    SET name = %s, price = %s, max_streams = %s
                    WHERE plan_id = %s
                    """,
                    (name, price, max_streams, plan_id),
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


def createModifyPaymentInfo(user_id: int, amount: float, status: str = "Pending"):
    """Insert into Payments table."""
    with get_connection() as conn:
        with conn.cursor() as cur:
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
