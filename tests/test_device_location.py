"""
Tests for services/device_location.py
Run via: python tests/test_runner.py
"""
import unittest
from db.connection import get_connection
from services.device_location import addDeviceByEmail, listDevices, markDeviceTrusted


def _setup_user(email="testdevice@example.com", name="Device Test User"):
    """Insert prerequisite plan, status, and user. Returns user email."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO subscription_plan (name, price, max_streams) VALUES (%s, %s, %s) RETURNING plan_id;",
                ("Device Plan", 9.99, 2),
            )
            plan_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO account_status (status_name) VALUES (%s) RETURNING status_id;",
                ("active",),
            )
            status_id = cur.fetchone()[0]
            cur.execute(
                'INSERT INTO "user" (name, email, plan_id, status_id) VALUES (%s, %s, %s, %s);',
                (name, email, plan_id, status_id),
            )
    return email


def _cleanup():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM session;")
            cur.execute("DELETE FROM device;")
            cur.execute('DELETE FROM "user";')
            cur.execute("DELETE FROM subscription_plan;")
            cur.execute("DELETE FROM account_status;")


class TestAddDevice(unittest.TestCase):
    def setUp(self):
        _cleanup()
        self.email = _setup_user()

    def tearDown(self):
        _cleanup()

    def test_add_device_appears_in_list(self):
        addDeviceByEmail(self.email, "phone", "fp-phone-001")
        devices = listDevices(self.email)
        names = [d["name"] for d in devices]
        self.assertIn("phone", names)

    def test_add_multiple_devices(self):
        addDeviceByEmail(self.email, "phone", "fp-phone-001")
        addDeviceByEmail(self.email, "laptop", "fp-laptop-001")
        devices = listDevices(self.email)
        self.assertEqual(len(devices), 2)

    def test_add_device_unknown_user_raises(self):
        with self.assertRaises(ValueError):
            addDeviceByEmail("nobody@example.com", "phone", "fp-nobody-001")

    def test_duplicate_fingerprint_raises(self):
        addDeviceByEmail(self.email, "phone", "fp-dupe-001")
        with self.assertRaises(Exception):
            addDeviceByEmail(self.email, "laptop", "fp-dupe-001")


class TestListDevices(unittest.TestCase):
    def setUp(self):
        _cleanup()
        self.email = _setup_user()

    def tearDown(self):
        _cleanup()

    def test_empty_returns_list(self):
        result = listDevices(self.email)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_unknown_email_returns_empty(self):
        result = listDevices("ghost@example.com")
        self.assertEqual(result, [])

    def test_device_not_trusted_by_default(self):
        addDeviceByEmail(self.email, "tv", "fp-tv-001")
        devices = listDevices(self.email)
        self.assertFalse(devices[0]["is_trusted"])

    def test_fingerprint_not_in_response(self):
        addDeviceByEmail(self.email, "phone", "fp-secret-001")
        devices = listDevices(self.email)
        self.assertNotIn("device_fingerprint", devices[0])


class TestMarkDeviceTrusted(unittest.TestCase):
    def setUp(self):
        _cleanup()
        self.email = _setup_user()
        addDeviceByEmail(self.email, "phone", "fp-trust-001")

    def tearDown(self):
        _cleanup()

    def test_mark_trusted(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT device_id FROM device WHERE device_fingerprint = %s", ("fp-trust-001",))
                device_id = cur.fetchone()[0]
        markDeviceTrusted(device_id)
        devices = listDevices(self.email)
        phone = next(d for d in devices if d["name"] == "phone")
        self.assertTrue(phone["is_trusted"])
