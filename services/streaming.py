"""
Streaming Session & Enforcement APIs.
attemptStateSession, attemptStartSession, trackUserLoginLogoutByEmail,
createModifyWatchTime, listWatchHistoryByEmail.
"""
from db.connection import get_connection


def _get_user_id_by_email(cur, email: str):
    """Return (user_id, home_location_id, plan_id, status_name, max_streams) or None."""
    cur.execute(
        """
        SELECT u.user_id, u.home_location_id, u.plan_id, a.status_name, p.max_streams
        FROM "user" u
        JOIN subscription_plan p ON u.plan_id = p.plan_id
        JOIN account_status a ON u.status_id = a.status_id
        WHERE u.email = %s
        """,
        (email,),
    )
    return cur.fetchone()


def _get_approved_location_id(cur, latitude: float, longitude: float):
    """Return location_id if this lat/long is an approved location, else None."""
    cur.execute(
        "SELECT location_id FROM location WHERE latitude = %s AND longitude = %s",
        (latitude, longitude),
    )
    row = cur.fetchone()
    return row[0] if row else None


def attemptStartSession(
    email: str,
    device_fingerprint: str,
    latitude: float,
    longitude: float,
) -> bool:
    """
    Validates and initiates a streaming session by email: account status, device eligibility,
    geographic access, and plan stream limits. Returns True if session granted, False otherwise.
    Device is identified by its fingerprint.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            user_row = _get_user_id_by_email(cur, email)
            if not user_row:
                return False
            user_id, home_location_id, plan_id, status_name, max_streams = (
                user_row[0], user_row[1], user_row[2], user_row[3], user_row[4]
            )
            if status_name != "active":
                return False

            cur.execute(
                """
                SELECT device_id, last_seen_at_home FROM device
                WHERE device_fingerprint = %s AND user_id = %s
                """,
                (device_fingerprint, user_id),
            )
            dev_row = cur.fetchone()
            if not dev_row:
                return False
            device_id, last_seen_at_home = dev_row[0], dev_row[1]

            location_id = _get_approved_location_id(cur, latitude, longitude)
            if location_id is None:
                return False

            cur.execute(
                "SELECT COUNT(*) FROM session WHERE user_id = %s AND end_time IS NULL",
                (user_id,),
            )
            if cur.fetchone()[0] >= max_streams:
                return False

            if home_location_id is not None and location_id != home_location_id:
                if last_seen_at_home:
                    cur.execute(
                        """
                        SELECT 1 FROM device
                        WHERE device_id = %s AND last_seen_at_home >= NOW() - INTERVAL '30 days'
                        """,
                        (device_id,),
                    )
                    if cur.fetchone() is None:
                        return False

            cur.execute(
                """
                INSERT INTO session (user_id, device_id, location_id)
                VALUES (%s, %s, %s)
                """,
                (user_id, device_id, location_id),
            )
            return True


def trackUserLoginLogoutByEmail(email: str, action: str) -> None:
    """Records login/logout activity for the account identified by email. Stub: no login_logs table yet."""
    pass


def createModifyWatchTime(session_id: int, duration_seconds: int):
    """Update session set end_time based on duration (start_time + duration)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE session
                SET end_time = start_time + (%s || ' seconds')::interval
                WHERE session_id = %s
                """,
                (duration_seconds, session_id),
            )


def listWatchHistoryByEmail(email: str):
    """Returns watch history for the account identified by email as readable entries (no internal IDs)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT user_id FROM "user" WHERE email = %s', (email,))
            row = cur.fetchone()
            if not row:
                return []
            user_id = row[0]
            cur.execute(
                """
                SELECT s.start_time, s.end_time, l.description AS location_description, d.name AS device_name
                FROM session s
                JOIN location l ON s.location_id = l.location_id
                JOIN device d ON s.device_id = d.device_id
                WHERE s.user_id = %s
                ORDER BY s.start_time DESC
                """,
                (user_id,),
            )
            columns = [d[0] for d in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
