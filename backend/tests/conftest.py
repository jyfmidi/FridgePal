import os
import uuid

os.environ.setdefault("FRIDGE_PAL_JWT_SECRET", "test-secret-at-least-thirty-two-characters-long!!")
os.environ.setdefault("FRIDGE_PAL_DEMO_PASSWORD", "demo-pass-123")
os.environ.setdefault("FRIDGE_PAL_ADMIN_PASSWORD", "admin-pass-123")
os.environ.setdefault("FRIDGE_PAL_ADMIN_USERNAME", "admin")

# Use a unique in-memory SQLite database per test app instance to prevent
# state leakage between tests.
_test_db_counter = 0


def _fresh_database_url() -> str:
    global _test_db_counter
    _test_db_counter += 1
    return f"sqlite:///file:test_{uuid.uuid4().hex}_{_test_db_counter}?mode=memory&cache=shared&uri=true"


def _reset_settings():
    from app.config import get_settings

    get_settings.cache_clear()
    os.environ["DATABASE_URL"] = _fresh_database_url()


_reset_settings()
