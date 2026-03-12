"""
Test suite driver — discovers and runs all tests in the tests/ directory.
Run from project root: python tests/test_runner.py
"""
import unittest
import sys
import os
from pathlib import Path

# Ensure project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from db.connection import get_connection


def reset_schema():
    """Drop all tables and recreate from schema.sql to ensure a clean, up-to-date schema."""
    schema_path = Path(PROJECT_ROOT) / "db" / "schema.sql"
    schema_sql = schema_path.read_text()

    drop_sql = """
    DROP TABLE IF EXISTS sessions   CASCADE;
    DROP TABLE IF EXISTS payments   CASCADE;
    DROP TABLE IF EXISTS devices    CASCADE;
    DROP TABLE IF EXISTS users      CASCADE;
    DROP TABLE IF EXISTS locations  CASCADE;
    DROP TABLE IF EXISTS account_statuses CASCADE;
    DROP TABLE IF EXISTS subscription_plans CASCADE;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(drop_sql)
            cur.execute(schema_sql)

    print("Schema reset complete.")


if __name__ == "__main__":
    reset_schema()

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=os.path.dirname(os.path.abspath(__file__)), pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    sys.exit(0 if result.wasSuccessful() else 1)
