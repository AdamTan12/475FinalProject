"""Database connection context manager for PostgreSQL."""
import contextlib
import psycopg2
from config.settings import DATABASE_URL


@contextlib.contextmanager
def get_connection():
    """
    Context manager that yields a psycopg2 connection.
    On exit: commits if no exception, rolls back on exception, then closes.
    """
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
