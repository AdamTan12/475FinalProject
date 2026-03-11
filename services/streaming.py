"""
Streaming Session & Enforcement APIs.
attemptStateSession, attemptStartSession, trackUserLoginLogoutByEmail, createModifyWatchTime, listWatchHistoryByEmail.
"""
from typing import Optional

from db.connection import get_connection


def _get_user_id_by_email(cur, email: str):
    """Return (user_id, home_location_id, plan_id, account_status) or None."""
    cur.execute(
        """
        SELECT u.user_id, u.home_location_id, u.plan_id, u.account_status, p.max_streams
        FROM users u
        JOIN subscription_plans p ON u.plan_id = p.plan_id
        WHERE u.email = %s
        """,
        (email,),
    )
    return cur.fetchone()


def _get_or_create_location_id(cur, latitude: float, longitude: float) -> int:
    """Find or create location by lat/long; return location_id."""
    cur.execute(
        "SELECT location_id FROM locations WHERE latitude = %s AND longitude = %s",
        (latitude, longitude),
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO locations (latitude, longitude, description) VALUES (%s, %s, %s) RETURNING location_id",
        (latitude, longitude, f"({latitude}, {longitude})"),
    )
    return cur.fetchone()[0]


def attemptStateSession(
    email: str,
    device_name: Optional[str],
    latitude: float,
    longitude: float,
    ip_address: str,
) -> bool:
    """
    Validates and initiates a streaming session by email: account status, device eligibility,
    geographic access, and plan stream limits. Returns True if session granted, False otherwise.
    Device is identified by name when provided; otherwise the user's first device is used.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            user_row = _get_user_id_by_email(cur, email)
            if not user_row:
                return False
            user_id, home_location_id, plan_id, max_streams = (
                user_row[0], user_row[1], user_row[2], user_row[4]
            )
            if user_row[3] != "active":
                return False

            if device_name is not None:
                cur.execute(
                    """
                    SELECT device_id, last_seen_at_home FROM devices
                    WHERE user_id = %s AND name = %s
                    """,
                    (user_id, device_name),
                )
            else:
                cur.execute(
                    """
                    SELECT device_id, last_seen_at_home FROM devices
                    WHERE user_id = %s
                    ORDER BY device_id
                    LIMIT 1
                    """,
                    (user_id,),
                )
            dev_row = cur.fetchone()
            if not dev_row:
                return False
            device_id, last_seen_at_home = dev_row[0], dev_row[1]

            location_id = _get_or_create_location_id(cur, latitude, longitude)

            cur.execute(
                "SELECT COUNT(*) FROM sessions WHERE user_id = %s AND end_time IS NULL",
                (user_id,),
            )
            if cur.fetchone()[0] >= max_streams:
                return False

            if home_location_id is not None and location_id != home_location_id:
                if last_seen_at_home:
                    cur.execute(
                        """
                        SELECT 1 FROM devices
                        WHERE device_id = %s AND last_seen_at_home >= NOW() - INTERVAL '30 days'
                        """,
                        (device_id,),
                    )
                    if cur.fetchone() is None:
                        return False

            cur.execute(
                """
                INSERT INTO sessions (user_id, device_id, location_id, ip_address)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, device_id, location_id, ip_address),
            )
            return True


def attemptStartSession(
    email: str,
    latitude: float,
    longitude: float,
    ip_address: str,
) -> bool:
    """
    Validates and initiates a streaming session for a subscriber by verifying account status,
    device eligibility, geographic access rights, and plan-based stream limits before granting
    content access. Uses the user's first device. Returns True if session granted, False otherwise.
    """
    return attemptStateSession(email, None, latitude, longitude, ip_address)


def trackUserLoginLogoutByEmail(email: str, action: str) -> None:
    """Records login/logout activity for the account identified by email to the audit (login_logs)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"User not found: {email}")
            cur.execute(
                "INSERT INTO login_logs (user_id, action) VALUES (%s, %s)",
                (row[0], action),
            )


def createModifyWatchTime(session_id: int, duration_seconds: int):
    """Update Sessions set EndTime based on duration (StartTime + duration)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE sessions
                SET end_time = start_time + (%s || ' seconds')::interval
                WHERE session_id = %s
                """,
                (duration_seconds, session_id),
            )


def listWatchHistoryByEmail(email: str):
    """Returns watch history for the account identified by email as readable entries (no internal IDs)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            if not row:
                return []
            user_id = row[0]
            cur.execute(
                """
                SELECT s.start_time, s.end_time, l.description AS location_description, d.name AS device_name
                FROM sessions s
                JOIN locations l ON s.location_id = l.location_id
                JOIN devices d ON s.device_id = d.device_id
                WHERE s.user_id = %s
                ORDER BY s.start_time DESC
                """,
                (user_id,),
            )
            columns = [d[0] for d in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
