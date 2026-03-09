"""
Device & Location Intelligence APIs.
listDevices, listLocations, validateDeviceMFA.
"""
from db.connection import get_connection


def listDevices(user_id: int):
    """Select from Devices where UserID matches."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT device_id, user_id, name, is_trusted, last_seen_at_home, created_at, updated_at
                FROM devices
                WHERE user_id = %s
                ORDER BY device_id
                """,
                (user_id,),
            )
            columns = [d[0] for d in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def listLocations(user_id: int):
    """Select distinct Locations linked to user's Sessions."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT l.location_id, l.latitude, l.longitude, l.description, l.created_at
                FROM locations l
                JOIN sessions s ON s.location_id = l.location_id
                WHERE s.user_id = %s
                ORDER BY l.location_id
                """,
                (user_id,),
            )
            columns = [d[0] for d in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def validateDeviceMFA(device_id: int, location_id: int, user_home_location_id: int | None) -> bool:
    """
    Check if Device.IsTrusted is true. If false, or if LocationID != User.HomeLocationID, trigger MFA.
    Update Devices set IsTrusted = True upon success.
    Returns True if access allowed (trusted or MFA passed), False otherwise.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT is_trusted FROM devices WHERE device_id = %s",
                (device_id,),
            )
            row = cur.fetchone()
            if not row:
                return False
            is_trusted = row[0]
            at_home = user_home_location_id is not None and location_id == user_home_location_id
            if is_trusted and at_home:
                return True
            # Caller should trigger MFA; on success call markDeviceTrusted(device_id)
            return False


def markDeviceTrusted(device_id: int):
    """Mark device as trusted after successful MFA."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE devices SET is_trusted = TRUE, updated_at = NOW() WHERE device_id = %s",
                (device_id,),
            )
