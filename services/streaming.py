"""
Streaming Session & Enforcement APIs.
attemptStartSession, trackUserLoginLogout, createModifyWatchTime, listWatchHistory.
"""
from db.connection import get_connection

# Device selected by setDevice(); used by attemptStartSession when no device is passed.
_current_device_name: Optional[str] = None


def attemptStartSession(user_id: int, device_id: int, location_id: int) -> dict:
    """
    Concurrency: Check ActiveSessions < MaxConcurrentStreams.
    Household 30-Day Rule: If LocationID != HomeLocationID, check if
    Device.LastSeenAtHome > 30 days ago. If yes, Deny Access.
    Atomic Transaction (Check + Insert). Returns {allowed: bool, session_id?: int, reason?: str}.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT u.home_location_id, p.max_streams
                FROM users u
                JOIN subscription_plans p ON u.plan_id = p.plan_id
                WHERE u.user_id = %s
                """,
                (user_id,),
            )
            user_row = cur.fetchone()
            if not user_row:
                return {"allowed": False, "reason": "user not found"}
            home_location_id, max_streams = user_row[0], user_row[1]

            cur.execute(
                """
                SELECT COUNT(*) FROM sessions WHERE user_id = %s AND end_time IS NULL
                """,
                (user_id,),
            )
            active_count = cur.fetchone()[0]
            if active_count >= max_streams:
                return {"allowed": False, "reason": "max concurrent streams reached"}

            if home_location_id is not None and location_id != home_location_id:
                cur.execute(
                    """
                    SELECT last_seen_at_home FROM devices WHERE device_id = %s
                    """,
                    (device_id,),
                )
                dev_row = cur.fetchone()
                if dev_row and dev_row[0]:
                    cur.execute(
                        """
                        SELECT 1 FROM devices
                        WHERE device_id = %s AND last_seen_at_home >= NOW() - INTERVAL '30 days'
                        """,
                        (device_id,),
                    )
                    if cur.fetchone() is None:
                        return {"allowed": False, "reason": "30-day household rule"}

            cur.execute(
                """
                INSERT INTO sessions (user_id, device_id, location_id)
                VALUES (%s, %s, %s)
                RETURNING session_id
                """,
                (user_id, device_id, location_id),
            )
            session_id = cur.fetchone()[0]
            return {"allowed": True, "session_id": session_id}


def trackUserLoginLogout(user_id: int, action: str):
    """Insert into system logs (or Sessions for streaming login). Stub: add login_logs table to persist."""
    # TODO: create login_logs (user_id, action, created_at) and INSERT here
    pass
def setDevice(device_name: Optional[str]) -> None:
    """
    Set the device to use for subsequent attemptStartSession calls.
    Pass a device name to use that device, or None to use the user's first device (default).
    """
    global _current_device_name
    _current_device_name = device_name


def attemptStartSession(
    email: str,
    latitude: float,
    longitude: float,
    ip_address: str,
) -> bool:
    """
    Validates and initiates a streaming session for a subscriber by verifying account status,
    device eligibility, geographic access rights, and plan-based stream limits before granting
    content access. Uses the device set by setDevice() if any, otherwise the user's first device.
    Returns True if session granted, False otherwise.
    """
    return attemptStateSession(email, _current_device_name, latitude, longitude, ip_address)


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


def listWatchHistory(user_id: int):
    """Select from Sessions (Start/End Time) joined with Locations and Devices."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.session_id, s.start_time, s.end_time,
                       l.location_id, l.description AS location_description,
                       d.device_id, d.name AS device_name
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
