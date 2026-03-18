"""
Device & Location Intelligence APIs.
addDeviceToAccount, addDeviceByEmail, addLocation,
listDevicesByEmail, listDevices, listLocations, listLocationsByEmail, markDeviceTrusted.
"""
from db.connection import get_connection


def addDeviceToAccount(
    email: str,
    deviceName: str,
    deviceType: str,
    deviceFingerprint: str,
    is_trusted: bool = False
) -> int:
    """Add a device for the user identified by email. Returns the new device_id."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT user_id FROM "user" WHERE email = %s', (email,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"User not found: {email}")
            user_id = row[0]
            cur.execute(
                """
                INSERT INTO device (user_id, name, device_type, device_fingerprint, is_trusted)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING device_id
                """,
                (user_id, deviceName, deviceType, deviceFingerprint, is_trusted),
            )
            return cur.fetchone()[0]


def addDeviceByEmail(email: str, name: str, device_fingerprint: str, is_trusted: bool = False) -> None:
    """Add a device for the user identified by email, storing the provided fingerprint."""
    addDeviceToAccount(email, name, None, device_fingerprint, is_trusted)


def addLocation(latitude: float, longitude: float) -> int:
    """Add a location by latitude/longitude. Returns the location_id of the new row."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO location (latitude, longitude)
                VALUES (%s, %s)
                RETURNING location_id
                """,
                (latitude, longitude),
            )
            return cur.fetchone()[0]


def listDevicesByEmail(email: str):
    """Select from device for the user identified by email. Includes device_id and device_type."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT user_id FROM "user" WHERE email = %s', (email,))
            row = cur.fetchone()
            if not row:
                return []
            user_id = row[0]
            cur.execute(
                """
                SELECT device_id, name, device_type, is_trusted, last_seen_at_home, created_at, updated_at
                FROM device
                WHERE user_id = %s
                ORDER BY created_at
                """,
                (user_id,),
            )
            columns = [d[0] for d in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]


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


def listLocationsByEmail(email: str):
    """Locations the account has streamed from (sessions) plus the account's home location."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT user_id, home_location_id FROM "user" WHERE email = %s',
                (email,),
            )
            row = cur.fetchone()
            if not row:
                return []
            user_id, home_location_id = row[0], row[1]
            cur.execute(
                """
                SELECT DISTINCT l.latitude, l.longitude, l.description, l.created_at
                FROM location l
                JOIN session s ON s.location_id = l.location_id
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
            if home_location_id is not None:
                cur.execute(
                    """
                    SELECT latitude, longitude, description, created_at
                    FROM location WHERE location_id = %s
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
