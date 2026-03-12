"""
Device & Location Intelligence APIs.
addDeviceByEmail, listDevices, listLocations.
"""
from db.connection import get_connection


def addDeviceByEmail(email: str, name: str, device_fingerprint: str) -> None:
    """Add a device for the user identified by email, storing the provided fingerprint."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT user_id FROM "user" WHERE email = %s', (email,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"User not found: {email}")
            user_id = row[0]
            cur.execute(
                """
                INSERT INTO device (user_id, name, device_fingerprint)
                VALUES (%s, %s, %s)
                """,
                (user_id, name, device_fingerprint),
            )


def listDevices(email: str):
    """Select from device for the user identified by email."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT user_id FROM "user" WHERE email = %s', (email,))
            row = cur.fetchone()
            if not row:
                return []
            user_id = row[0]
            cur.execute(
                """
                SELECT name, is_trusted, last_seen_at_home, created_at, updated_at
                FROM device
                WHERE user_id = %s
                ORDER BY created_at
                """,
                (user_id,),
            )
            columns = [d[0] for d in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def listLocations(email: str):
    """Select distinct locations linked to user's sessions. User identified by email."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT user_id FROM "user" WHERE email = %s', (email,))
            row = cur.fetchone()
            if not row:
                return []
            user_id = row[0]
            cur.execute(
                """
                SELECT DISTINCT l.latitude, l.longitude, l.description, l.created_at
                FROM location l
                JOIN session s ON s.location_id = l.location_id
                WHERE s.user_id = %s
                ORDER BY l.description
                """,
                (user_id,),
            )
            columns = [d[0] for d in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def markDeviceTrusted(device_id: int):
    """Mark device as trusted after successful MFA."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE device SET is_trusted = TRUE, updated_at = NOW() WHERE device_id = %s",
                (device_id,),
            )
