"""
Tests for services/device_location.py
Run via: python tests/test_runner.py
"""
import unittest
from db.connection import get_connection
from services.device_location import (
    addDeviceToAccount,
    addDeviceByEmail,
    addLocation,
    listDevicesByEmail,
    markDeviceTrusted,
)


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
            cur.execute("DELETE FROM location;")
            cur.execute("DELETE FROM subscription_plan;")
            cur.execute("DELETE FROM account_status;")


class TestAddDevice(unittest.TestCase):
    def setUp(self):
        _cleanup()
        self.email = _setup_user()

    def tearDown(self):
        _cleanup()

    def test_add_device_appears_in_list(self):
        addDeviceToAccount(self.email, "phone", "mobile", "fp-phone-001")
        devices = listDevicesByEmail(self.email)
        names = [d["name"] for d in devices]
        self.assertIn("phone", names)

    def test_add_device_returns_device_id(self):
        device_id = addDeviceToAccount(self.email, "laptop", "desktop", "fp-laptop-001")
        self.assertIsInstance(device_id, int)
        self.assertGreater(device_id, 0)

    def test_add_multiple_devices(self):
        addDeviceToAccount(self.email, "phone", "mobile", "fp-phone-001")
        addDeviceToAccount(self.email, "laptop", "desktop", "fp-laptop-001")
        devices = listDevicesByEmail(self.email)
        self.assertEqual(len(devices), 2)

    def test_add_device_unknown_user_raises(self):
        with self.assertRaises(ValueError):
            addDeviceToAccount("nobody@example.com", "phone", "mobile", "fp-nobody-001")

    def test_duplicate_fingerprint_raises(self):
        addDeviceToAccount(self.email, "phone", "mobile", "fp-dupe-001")
        with self.assertRaises(Exception):
            addDeviceToAccount(self.email, "laptop", "desktop", "fp-dupe-001")

    def test_add_device_by_email_legacy(self):
        addDeviceByEmail(self.email, "tv", "fp-tv-legacy-001")
        devices = listDevicesByEmail(self.email)
        names = [d["name"] for d in devices]
        self.assertIn("tv", names)


class TestListDevices(unittest.TestCase):
    def setUp(self):
        _cleanup()
        self.email = _setup_user()

    def tearDown(self):
        _cleanup()

    def test_empty_returns_list(self):
        result = listDevicesByEmail(self.email)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_unknown_email_returns_empty(self):
        result = listDevicesByEmail("ghost@example.com")
        self.assertEqual(result, [])

    def test_device_not_trusted_by_default(self):
        addDeviceToAccount(self.email, "tv", "tv", "fp-tv-001")
        devices = listDevicesByEmail(self.email)
        self.assertFalse(devices[0]["is_trusted"])

    def test_fingerprint_not_in_response(self):
        addDeviceToAccount(self.email, "phone", "mobile", "fp-secret-001")
        devices = listDevicesByEmail(self.email)
        self.assertNotIn("device_fingerprint", devices[0])


class TestAddLocation(unittest.TestCase):
    def setUp(self):
        _cleanup()

    def tearDown(self):
        _cleanup()

    def test_add_location_returns_location_id(self):
        location_id = addLocation(47.6062, -122.3321)
        self.assertIsInstance(location_id, int)
        self.assertGreater(location_id, 0)

    def test_add_location_persists(self):
        location_id = addLocation(40.7128, -74.0060)
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT location_id FROM location WHERE latitude = 40.7128 AND longitude = -74.0060"
                )
                row = cur.fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row[0], location_id)


class TestMarkDeviceTrusted(unittest.TestCase):
    def setUp(self):
        _cleanup()
        self.email = _setup_user()
        addDeviceToAccount(self.email, "phone", "mobile", "fp-trust-001")

    def tearDown(self):
        _cleanup()

    def test_mark_trusted(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT device_id FROM device WHERE device_fingerprint = %s", ("fp-trust-001",))
                device_id = cur.fetchone()[0]
        markDeviceTrusted(device_id)
        devices = listDevicesByEmail(self.email)
        phone = next(d for d in devices if d["name"] == "phone")
        self.assertTrue(phone["is_trusted"])
