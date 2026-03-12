"""
Reporting APIs.
reportTotalActiveSessions, reportSuspiciousActivity.
"""
from db.connection import get_connection


def reportTotalActiveSessions() -> int:
    """Count total sessions where end_time is NULL (active sessions)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM session WHERE end_time IS NULL")
            row = cur.fetchone()
            return row[0] if row else 0


def reportSuspiciousActivity():
    """Return list of emails for accounts with more than 2 active sessions."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT u.email
                FROM "user" u
                JOIN (
                    SELECT user_id
                    FROM session
                    WHERE end_time IS NULL
                    GROUP BY user_id
                    HAVING COUNT(*) > 2
                ) active ON active.user_id = u.user_id
                """
            )
            return [row[0] for row in cur.fetchall()]
