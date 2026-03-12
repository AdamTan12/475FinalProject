"""
Account & Subscription Management APIs.
createUserAccount, updateUserByEmail, listUserAccounts, createSubscriptionPlan,
modifySubscriptionPlan, querySubscriptionPlan, listSubscriptionPlans.
"""
import psycopg2
from db.connection import get_connection


def createUserAccount(
    name: str,
    email: str,
    planName: str,
    latitude: float = None,
    longitude: float = None,
) -> bool:
    """
    Create a user account with plan name and optional home location (lat/long).
    Finds or inserts a location row and uses its ID as home_location_id.
    Returns True on success, False if name or email is not unique (or plan not found).
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT plan_id FROM subscription_plans WHERE name = %s", (planName,))
                plan_row = cur.fetchone()
                if not plan_row:
                    return False
                cur.execute("SELECT status_id FROM account_statuses WHERE status_name = %s", ("active",))
                status_row = cur.fetchone()
                if not status_row:
                    return False

                home_location_id = None
                if latitude is not None and longitude is not None:
                    cur.execute(
                        "SELECT location_id FROM locations WHERE latitude = %s AND longitude = %s",
                        (latitude, longitude),
                    )
                    loc_row = cur.fetchone()
                    if loc_row:
                        home_location_id = loc_row[0]
                    else:
                        cur.execute(
                            """
                            INSERT INTO locations (latitude, longitude)
                            VALUES (%s, %s)
                            RETURNING location_id
                            """,
                            (latitude, longitude),
                        )
                        home_location_id = cur.fetchone()[0]

                cur.execute(
                    """
                    INSERT INTO users (name, email, plan_id, status_id, home_location_id)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (name, email, plan_row[0], status_row[0], home_location_id),
                )
        return True
    except psycopg2.IntegrityError:
        return False


def createUser(name: str, email: str, plan_id: int, status_id: int):
    """
    Create Users (internal/legacy).
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


def updateUserByEmail(
    email: str,
    newName: str,
    newPlanName: str,
    newAccountStatus: str,
    homeLocID: int = None,
) -> bool:
    """Update a user identified by email, resolving plan and status by name. Returns True if updated."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT plan_id FROM subscription_plans WHERE name = %s", (newPlanName,))
            plan_row = cur.fetchone()
            if not plan_row:
                return False
            cur.execute("SELECT status_id FROM account_statuses WHERE status_name = %s", (newAccountStatus,))
            status_row = cur.fetchone()
            if not status_row:
                return False
            cur.execute(
                """
                UPDATE users SET name = %s, plan_id = %s, status_id = %s, home_location_id = %s, updated_at = NOW()
                WHERE email = %s
                """,
                (newName, plan_row[0], status_row[0], homeLocID, email),
            )
            return cur.rowcount == 1


def modifySubscriptionPlan(name: str, price: float, max_streams: int) -> bool:
    """Update a subscription plan identified by name. Returns True if at least one row updated."""
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
            return cur.rowcount >= 1


def createSubscriptionPlan(name: str, price: float, max_streams: int) -> bool:
    """
    Create or adjust subscription plan by name (upsert). Returns True on success, False on failure.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT plan_id FROM subscription_plans WHERE name = %s", (name,))
                if cur.fetchone():
                    cur.execute(
                        """
                        UPDATE subscription_plans SET price = %s, max_streams = %s WHERE name = %s
                        """,
                        (price, max_streams, name),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO subscription_plans (name, price, max_streams)
                        VALUES (%s, %s, %s)
                        """,
                        (name, price, max_streams),
                    )
        return True
    except psycopg2.IntegrityError:
        return False



def querySubscriptionPlan(planID: int):
    """Return plan object for the given plan_id, or None if not found."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT plan_id, name, price, max_streams
                FROM subscription_plans
                WHERE plan_id = %s
                """,
                (planID,),
            )
            row = cur.fetchone()
            if not row:
                return None
            columns = [d[0] for d in cur.description]
            return dict(zip(columns, row))


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


