"""
Tests for services/account_subscription.py
Run via: python tests/test_runner.py
"""
import unittest
from db.connection import get_connection
from services.account_subscription import (
    createUser,
    createUserAccount,
    modifyUser,
    updateUserByEmail,
    listUserAccounts,
    createSubscriptionPlan,
    modifySubscriptionPlan,
    querySubscriptionPlan,
    listSubscriptionPlans,
)


def _setup_prerequisites():
    """Insert a plan and status needed for user FK constraints. Returns (plan_id, status_id)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO subscription_plan (name, price, max_streams) VALUES (%s, %s, %s) RETURNING plan_id;",
                ("Test Plan", 9.99, 1),
            )
            plan_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO account_status (status_name) VALUES (%s) RETURNING status_id;",
                ("active",),
            )
            status_id = cur.fetchone()[0]
    return plan_id, status_id


def _cleanup():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM payment;")
            cur.execute("DELETE FROM session;")
            cur.execute("DELETE FROM device;")
            cur.execute('DELETE FROM "user";')
            cur.execute("DELETE FROM location;")
            cur.execute("DELETE FROM subscription_plan;")
            cur.execute("DELETE FROM account_status;")


class TestCreateUser(unittest.TestCase):
    def setUp(self):
        _cleanup()
        self.plan_id, self.status_id = _setup_prerequisites()

    def tearDown(self):
        _cleanup()

    def test_create_user_appears_in_list(self):
        createUser("Alice", "alice@example.com", self.plan_id, self.status_id)
        users = listUserAccounts()
        emails = [u["email"] for u in users]
        self.assertIn("alice@example.com", emails)

    def test_create_user_fields(self):
        createUser("Bob", "bob@example.com", self.plan_id, self.status_id)
        users = listUserAccounts()
        bob = next(u for u in users if u["email"] == "bob@example.com")
        self.assertEqual(bob["name"], "Bob")
        self.assertEqual(bob["plan_id"], self.plan_id)
        self.assertEqual(bob["status_id"], self.status_id)


class TestCreateUserAccount(unittest.TestCase):
    def setUp(self):
        _cleanup()
        _setup_prerequisites()

    def tearDown(self):
        _cleanup()

    def test_create_user_account_success(self):
        ok = createUserAccount("Alice2", "alice2@example.com", "Test Plan", 47.0, -122.0)
        self.assertTrue(ok)
        users = listUserAccounts()
        emails = [u["email"] for u in users]
        self.assertIn("alice2@example.com", emails)

    def test_create_user_account_with_lat_long_sets_home_location(self):
        ok = createUserAccount("BobHome", "bobhome@example.com", "Test Plan", 40.7128, -74.0060)
        self.assertTrue(ok)
        users = listUserAccounts()
        bob = next(u for u in users if u["email"] == "bobhome@example.com")
        self.assertIsNotNone(bob["home_location_id"])

    def test_create_user_account_duplicate_name_returns_false(self):
        createUserAccount("Dave", "dave1@example.com", "Test Plan", None, None)
        ok = createUserAccount("Dave", "dave2@example.com", "Test Plan", None, None)
        self.assertFalse(ok)

    def test_create_user_account_duplicate_email_returns_false(self):
        createUserAccount("Eve1", "eve@example.com", "Test Plan", None, None)
        ok = createUserAccount("Eve2", "eve@example.com", "Test Plan", None, None)
        self.assertFalse(ok)

    def test_create_user_account_unknown_plan_returns_false(self):
        ok = createUserAccount("Frank", "frank@example.com", "Nonexistent Plan", None, None)
        self.assertFalse(ok)


class TestModifyUser(unittest.TestCase):
    def setUp(self):
        _cleanup()
        self.plan_id, self.status_id = _setup_prerequisites()
        createUser("Carol", "carol@example.com", self.plan_id, self.status_id)

    def tearDown(self):
        _cleanup()

    def test_modify_user_by_email(self):
        modifyUser("Carol Updated", "carol@example.com", self.plan_id, self.status_id)
        users = listUserAccounts()
        carol = next(u for u in users if u["email"] == "carol@example.com")
        self.assertEqual(carol["name"], "Carol Updated")

    def test_modify_user_by_user_id(self):
        users = listUserAccounts()
        carol = next(u for u in users if u["email"] == "carol@example.com")
        modifyUser("Carol ID Updated", "carol@example.com", self.plan_id, self.status_id, user_id=carol["user_id"])
        users = listUserAccounts()
        carol = next(u for u in users if u["email"] == "carol@example.com")
        self.assertEqual(carol["name"], "Carol ID Updated")


class TestUpdateUserByEmail(unittest.TestCase):
    def setUp(self):
        _cleanup()
        self.plan_id, self.status_id = _setup_prerequisites()
        createUser("Gina", "gina@example.com", self.plan_id, self.status_id)

    def tearDown(self):
        _cleanup()

    def test_update_user_by_email_returns_true(self):
        ok = updateUserByEmail("gina@example.com", "Gina New", "Test Plan", "active", None)
        self.assertTrue(ok)
        users = listUserAccounts()
        gina = next(u for u in users if u["email"] == "gina@example.com")
        self.assertEqual(gina["name"], "Gina New")

    def test_update_user_by_email_unknown_email_returns_false(self):
        ok = updateUserByEmail("unknown@example.com", "X", "Test Plan", "active", None)
        self.assertFalse(ok)


class TestListUserAccounts(unittest.TestCase):
    def setUp(self):
        _cleanup()
        self.plan_id, self.status_id = _setup_prerequisites()

    def tearDown(self):
        _cleanup()

    def test_empty_returns_list(self):
        result = listUserAccounts()
        self.assertIsInstance(result, list)

    def test_returns_all_users(self):
        createUser("User1", "u1@example.com", self.plan_id, self.status_id)
        createUser("User2", "u2@example.com", self.plan_id, self.status_id)
        users = listUserAccounts()
        self.assertEqual(len(users), 2)


class TestQuerySubscriptionPlan(unittest.TestCase):
    def setUp(self):
        _cleanup()

    def tearDown(self):
        _cleanup()

    def test_query_plan_returns_plan_object(self):
        createSubscriptionPlan("QueryPlan", 12.99, 2)
        plans = listSubscriptionPlans()
        p = next(pl for pl in plans if pl["name"] == "QueryPlan")
        plan = querySubscriptionPlan(p["plan_id"])
        self.assertIsNotNone(plan)
        self.assertEqual(plan["name"], "QueryPlan")
        self.assertAlmostEqual(float(plan["price"]), 12.99, places=2)
        self.assertEqual(plan["max_streams"], 2)

    def test_query_plan_not_found_returns_none(self):
        plan = querySubscriptionPlan(99999)
        self.assertIsNone(plan)


class TestSubscriptionPlans(unittest.TestCase):
    def setUp(self):
        _cleanup()

    def tearDown(self):
        _cleanup()

    def test_create_plan_appears_in_list(self):
        ok = createSubscriptionPlan("Gold", 29.99, 5)
        self.assertTrue(ok)
        plans = listSubscriptionPlans()
        names = [p["name"] for p in plans]
        self.assertIn("Gold", names)

    def test_modify_plan(self):
        createSubscriptionPlan("Silver", 19.99, 3)
        ok = modifySubscriptionPlan("Silver", 21.99, 3)
        self.assertTrue(ok)
        plans = listSubscriptionPlans()
        silver = next(p for p in plans if p["name"] == "Silver")
        self.assertAlmostEqual(float(silver["price"]), 21.99, places=2)

    def test_modify_plan_nonexistent_returns_false(self):
        ok = modifySubscriptionPlan("NoSuchPlan", 9.99, 1)
        self.assertFalse(ok)
