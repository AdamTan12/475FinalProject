"""
Device & Location Intelligence APIs.
addDeviceByEmail, listDevices, listLocations.
"""
from typing import Optional

from db.connection import get_connection


def addDeviceByEmail(email: str, name: str) -> None:
    """Add a device for the user identified by email."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"User not found: {email}")
            user_id = row[0]
            cur.execute(
                """
                INSERT INTO devices (user_id, name)
                VALUES (%s, %s)
                """,
                (user_id, name),
            )


def listDevices(email: str):
    """Select from Devices for the user identified by email. Does not expose user_id or device_id."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            if not row:
                return []
            user_id = row[0]
            cur.execute(
                """
                SELECT name, is_trusted, last_seen_at_home, created_at, updated_at
                FROM devices
                WHERE user_id = %s
                ORDER BY created_at
                """,
                (user_id,),
            )
            columns = [d[0] for d in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def listLocations(email: str):
    """Select distinct Locations linked to user's Sessions. User identified by email."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            if not row:
                return []
            user_id = row[0]
            cur.execute(
                """
                SELECT DISTINCT l.latitude, l.longitude, l.description, l.created_at
                FROM locations l
                JOIN sessions s ON s.location_id = l.location_id
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
                "UPDATE devices SET is_trusted = TRUE, updated_at = NOW() WHERE device_id = %s",
                (device_id,),
            )
