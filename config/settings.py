"""Load DB URL and other settings from environment."""
import os
from pathlib import Path

# Load .env if present (optional)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://localhost:5432/streaming_db",
)
