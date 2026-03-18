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
    """Return list of emails for accounts with active sessions exceeding their plan's max_streams."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT u.email
                FROM "user" u
                JOIN subscription_plan p ON u.plan_id = p.plan_id
                JOIN (
                    SELECT user_id, COUNT(*) AS active_count
                    FROM session
                    WHERE end_time IS NULL
                    GROUP BY user_id
                ) active ON active.user_id = u.user_id
                WHERE active.active_count > p.max_streams
                """
            )
            return [row[0] for row in cur.fetchall()]
