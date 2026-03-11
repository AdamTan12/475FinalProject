"""
Tests for services/account_subscription.py
Run via: python tests/test_runner.py
"""
import unittest
from db.connection import get_connection
from services.account_subscription import (
    createUser,
    modifyUser,
    listUserAccounts,
    createSubscriptionPlan,
    modifySubscriptionPlan,
    listSubscriptionPlans,
)


def _setup_prerequisites():
    """Insert a plan and status needed for user FK constraints. Returns (plan_id, status_id)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO subscription_plans (name, price, max_streams) VALUES (%s, %s, %s) RETURNING plan_id;",
                ("Test Plan", 9.99, 1),
            )
            plan_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO account_statuses (status_name) VALUES (%s) RETURNING status_id;",
                ("active",),
            )
            status_id = cur.fetchone()[0]
    return plan_id, status_id


def _cleanup():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM payments;")
            cur.execute("DELETE FROM sessions;")
            cur.execute("DELETE FROM devices;")
            cur.execute("DELETE FROM users;")
            cur.execute("DELETE FROM subscription_plans;")
            cur.execute("DELETE FROM account_statuses;")


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


class TestSubscriptionPlans(unittest.TestCase):
    def setUp(self):
        _cleanup()

    def tearDown(self):
        _cleanup()

    def test_create_plan_appears_in_list(self):
        createSubscriptionPlan("Gold", 29.99, 5)
        plans = listSubscriptionPlans()
        names = [p["name"] for p in plans]
        self.assertIn("Gold", names)

    def test_modify_plan(self):
        createSubscriptionPlan("Silver", 19.99, 3)
        plans = listSubscriptionPlans()
        silver = next(p for p in plans if p["name"] == "Silver")
        modifySubscriptionPlan("Silver", 21.99, 3)
        plans = listSubscriptionPlans()
        silver = next(p for p in plans if p["name"] == "Silver")
        self.assertAlmostEqual(float(silver["price"]), 21.99, places=2)


