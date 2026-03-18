"""
Streaming Session & Enforcement APIs.
attemptStartSession, attemptEndSession,
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
) -> tuple:
    """
    Validates and initiates a streaming session. Returns (granted: bool, reason: str | None).
    When granted is False, reason describes why.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            user_row = _get_user_id_by_email(cur, email)
            if not user_row:
                return (False, "User not found for this email.")
            user_id, home_location_id, plan_id, status_name, max_streams = (
                user_row[0], user_row[1], user_row[2], user_row[3], user_row[4]
            )
            if status_name != "active":
                return (False, "Account is not active.")

            cur.execute(
                """
                SELECT device_id, last_seen_at_home, is_trusted FROM device
                WHERE device_fingerprint = %s AND user_id = %s
                """,
                (device_fingerprint, user_id),
            )
            dev_row = cur.fetchone()
            if not dev_row:
                return (
                    False,
                    "Device not registered to this account. Add the device first via addDeviceToAccount.",
                )
            device_id, last_seen_at_home, is_trusted = dev_row[0], dev_row[1], dev_row[2]

            location_id = _get_approved_location_id(cur, latitude, longitude)
            if location_id is None:
                return (
                    False,
                    "This location is not in the database. Add it first via addLocation(latitude, longitude).",
                )

            cur.execute(
                "SELECT COUNT(*) FROM session WHERE user_id = %s AND end_time IS NULL",
                (user_id,),
            )
            active_count = cur.fetchone()[0]
            if active_count >= max_streams:
                return (False, f"Stream limit reached ({active_count}/{max_streams} active sessions).")

            if not is_trusted and home_location_id is not None and location_id != home_location_id:
                if last_seen_at_home:
                    cur.execute(
                        """
                        SELECT 1 FROM device
                        WHERE device_id = %s AND last_seen_at_home >= NOW() - INTERVAL '30 days'
                        """,
                        (device_id,),
                    )
                    if cur.fetchone() is None:
                        return (
                            False,
                            "Streaming from a non-home location is not allowed; device has not been seen at home in the last 30 days.",
                        )

            cur.execute(
                """
                INSERT INTO session (user_id, device_id, location_id)
                VALUES (%s, %s, %s)
                """,
                (user_id, device_id, location_id),
            )
            return (True, None)


def attemptEndSession(email: str, deviceFingerprint: str) -> bool:
    """
    End the active streaming session for the given email and device.
    Returns True if a session was closed, False otherwise.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT user_id FROM "user" WHERE email = %s', (email,))
            row = cur.fetchone()
            if not row:
                return False
            user_id = row[0]
            cur.execute(
                "SELECT device_id FROM device WHERE device_fingerprint = %s AND user_id = %s",
                (deviceFingerprint, user_id),
            )
            dev_row = cur.fetchone()
            if not dev_row:
                return False
            device_id = dev_row[0]
            cur.execute(
                """
                UPDATE session SET end_time = NOW()
                WHERE user_id = %s AND device_id = %s AND end_time IS NULL
                """,
                (user_id, device_id),
            )
            return cur.rowcount >= 1

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
