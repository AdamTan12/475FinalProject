"""
Reporting APIs.
reportTotalActiveSessions, reportSuspiciousActivity.
"""
from db.connection import get_connection


def reportTotalActiveSessions() -> int:
    """Count Sessions where EndTime is NULL."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, COUNT(*) FROM sessions WHERE end_time IS NULL GROUP BY user_id"
            )
            row = cur.fetchone()
            return row[0] if row else 0


def reportSuspiciousActivity():
    """Find users with active sessions in >2 distinct locations simultaneously."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id, COUNT(DISTINCT location_id) AS location_count
                FROM sessions
                WHERE end_time IS NULL
                GROUP BY user_id
                HAVING COUNT(DISTINCT location_id) > 2
                """
            )
            columns = [d[0] for d in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
