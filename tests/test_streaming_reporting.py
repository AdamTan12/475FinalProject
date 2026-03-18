"""
Tests for services/streaming.py (attemptEndSession) and services/reporting.py.
Run via: python tests/test_runner.py
"""
import unittest
from db.connection import get_connection
from services import streaming, reporting


def _cleanup():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM session;")
            cur.execute("DELETE FROM device;")
            cur.execute('DELETE FROM "user";')
            cur.execute("DELETE FROM location;")
            cur.execute("DELETE FROM subscription_plan;")
            cur.execute("DELETE FROM account_status;")


def _setup_user_and_device(email="stream@example.com", plan_name="Basic", max_streams=2):
    """Create plan, status, user, location, and device. Returns (email, location_id, device_fingerprint)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO subscription_plan (name, price, max_streams) VALUES (%s, %s, %s) RETURNING plan_id;",
                (plan_name, 9.99, max_streams),
            )
            plan_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO account_status (status_name) VALUES (%s) RETURNING status_id;",
                ("active",),
            )
            status_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO location (latitude, longitude) VALUES (47.0, -122.0) RETURNING location_id;"
            )
            location_id = cur.fetchone()[0]
            cur.execute(
                'INSERT INTO "user" (name, email, plan_id, status_id, home_location_id) VALUES (%s, %s, %s, %s, %s);',
                ("Stream User", email, plan_id, status_id, location_id),
            )
            cur.execute('SELECT user_id FROM "user" WHERE email = %s;', (email,))
            user_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO device (user_id, name, device_type, device_fingerprint) VALUES (%s, %s, %s, %s);",
                (user_id, "phone", "mobile", "fp-stream-001"),
            )
    return email, location_id, "fp-stream-001"


class TestAttemptEndSession(unittest.TestCase):
    def setUp(self):
        _cleanup()
        self.email, self.location_id, self.device_fp = _setup_user_and_device()

    def tearDown(self):
        _cleanup()

    def test_attempt_end_session_closes_active_session(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT user_id FROM "user" WHERE email = %s', (self.email,))
                user_id = cur.fetchone()[0]
                cur.execute(
                    "SELECT device_id FROM device WHERE device_fingerprint = %s",
                    (self.device_fp,),
                )
                device_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO session (user_id, device_id, location_id) VALUES (%s, %s, %s)",
                    (user_id, device_id, self.location_id),
                )
        ok = streaming.attemptEndSession(self.email, self.device_fp)
        self.assertTrue(ok)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT COUNT(*) FROM session WHERE user_id = (SELECT user_id FROM "user" WHERE email = %s) AND end_time IS NOT NULL',
                    (self.email,),
                )
                self.assertEqual(cur.fetchone()[0], 1)

    def test_attempt_end_session_no_active_session_returns_false(self):
        ok = streaming.attemptEndSession(self.email, self.device_fp)
        self.assertFalse(ok)

    def test_attempt_end_session_unknown_email_returns_false(self):
        ok = streaming.attemptEndSession("unknown@example.com", self.device_fp)
        self.assertFalse(ok)


class TestReportTotalActiveSessions(unittest.TestCase):
    def setUp(self):
        _cleanup()

    def tearDown(self):
        _cleanup()

    def test_report_total_active_sessions_empty_is_zero(self):
        count = reporting.reportTotalActiveSessions()
        self.assertEqual(count, 0)

    def test_report_total_active_sessions_counts_only_open_sessions(self):
        email, loc_id, dev_fp = _setup_user_and_device()
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT user_id FROM "user" WHERE email = %s', (email,))
                user_id = cur.fetchone()[0]
                cur.execute(
                    "SELECT device_id FROM device WHERE device_fingerprint = %s",
                    (dev_fp,),
                )
                device_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO session (user_id, device_id, location_id) VALUES (%s, %s, %s), (%s, %s, %s)",
                    (user_id, device_id, loc_id, user_id, device_id, loc_id),
                )
        count = reporting.reportTotalActiveSessions()
        self.assertEqual(count, 2)


class TestReportSuspiciousActivity(unittest.TestCase):
    def setUp(self):
        _cleanup()

    def tearDown(self):
        _cleanup()

    def test_report_suspicious_activity_empty_when_none(self):
        emails = reporting.reportSuspiciousActivity()
        self.assertEqual(emails, [])

    def test_report_suspicious_activity_returns_emails_with_more_than_two_active_sessions(self):
        email, loc_id, dev_fp = _setup_user_and_device(max_streams=2)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT user_id FROM "user" WHERE email = %s', (email,))
                user_id = cur.fetchone()[0]
                cur.execute(
                    "SELECT device_id FROM device WHERE device_fingerprint = %s",
                    (dev_fp,),
                )
                device_id = cur.fetchone()[0]
                for _ in range(3):
                    cur.execute(
                        "INSERT INTO session (user_id, device_id, location_id) VALUES (%s, %s, %s)",
                        (user_id, device_id, loc_id),
                    )
        emails = reporting.reportSuspiciousActivity()
        self.assertIsInstance(emails, list)
        self.assertIn(email, emails)
