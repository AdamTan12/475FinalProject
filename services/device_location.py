"""
Device & Location Intelligence APIs.
addDeviceToAccount, addLocation, listDevicesByEmail, listLocationsByEmail.
"""
from db.connection import get_connection


def addDeviceToAccount(
    email: str,
    deviceName: str,
    deviceType: str,
    deviceFingerprint: str,
) -> int:
    """Add a device for the user identified by email. Returns the new device_id (integer)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"User not found: {email}")
            user_id = row[0]
            cur.execute(
                """
                INSERT INTO devices (user_id, name, device_type, device_fingerprint)
                VALUES (%s, %s, %s, %s)
                RETURNING device_id
                """,
                (user_id, deviceName, deviceType, deviceFingerprint),
            )
            return cur.fetchone()[0]


def addLocation(latitude: float, longitude: float) -> int:
    """Add a location by latitude/longitude. Returns the location_id of the new row."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO locations (latitude, longitude)
                VALUES (%s, %s)
                RETURNING location_id
                """,
                (latitude, longitude),
            )
            return cur.fetchone()[0]


def addDeviceByEmail(email: str, name: str, device_fingerprint: str) -> None:
    """Add a device (legacy). Prefer addDeviceToAccount."""
    addDeviceToAccount(email, name, None, device_fingerprint)


def listDevicesByEmail(email: str):
    """Select from Devices for the user identified by email. Returns list of devices."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            if not row:
                return []
            user_id = row[0]
            cur.execute(
                """
                SELECT device_id, name, device_type, is_trusted, last_seen_at_home, created_at, updated_at
                FROM devices
                WHERE user_id = %s
                ORDER BY created_at
                """,
                (user_id,),
            )
            columns = [d[0] for d in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def listLocationsByEmail(email: str):
    """Locations the account has used the app from (sessions) plus the account's home location. Returns list of locations."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, home_location_id FROM users WHERE email = %s",
                (email,),
            )
            row = cur.fetchone()
            if not row:
                return []
            user_id, home_location_id = row[0], row[1]
            # Locations from sessions (where they've streamed from)
            cur.execute(
                """
                SELECT DISTINCT l.latitude, l.longitude, l.description, l.created_at
                FROM locations l
                JOIN sessions s ON s.location_id = l.location_id
                WHERE s.user_id = %s
                """,
                (user_id,),
            )
            seen = set()
            results = []
            columns = [d[0] for d in cur.description]
            for r in cur.fetchall():
                key = (r[0], r[1])
                if key not in seen:
                    seen.add(key)
                    results.append(dict(zip(columns, r)))
            # Include home location if set and not already in the list
            if home_location_id is not None:
                cur.execute(
                    """
                    SELECT latitude, longitude, description, created_at
                    FROM locations WHERE location_id = %s
                    """,
                    (home_location_id,),
                )
                home_row = cur.fetchone()
                if home_row and (home_row[0], home_row[1]) not in seen:
                    results.append(
                        dict(zip(["latitude", "longitude", "description", "created_at"], home_row))
                    )
            return sorted(
                results,
                key=lambda x: (str(x.get("description") or ""), str(x.get("created_at") or "")),
            )


def markDeviceTrusted(device_id: int):
    """Mark device as trusted after successful MFA."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE devices SET is_trusted = TRUE, updated_at = NOW() WHERE device_id = %s",
                (device_id,),
            )
