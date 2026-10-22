"""Shared test setup.

Normal runs use a throw-away SQLite file in a temp folder, so the real MySQL
database is never touched. The optional MySQL integration tests (see
test_mysql_integration.py) use a SEPARATE database whose name must end in
"_test".
"""
import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app import create_app  # noqa: E402


def mysql_test_settings():
    """Settings for the optional MySQL integration tests, or None."""
    name = os.environ.get("TEST_DB_NAME", "")
    user = os.environ.get("TEST_DB_USER", "")
    password = os.environ.get("TEST_DB_PASSWORD")
    if not (name and user and password is not None):
        return None
    if not name.endswith("_test"):
        raise RuntimeError("TEST_DB_NAME must end with '_test' to protect real data.")
    return {"DB_BACKEND": "mysql", "DB_HOST": os.environ.get("TEST_DB_HOST", "localhost"),
            "DB_PORT": int(os.environ.get("TEST_DB_PORT", "3306")),
            "DB_USER": user, "DB_PASSWORD": password, "DB_NAME": name}


class AppTestCase(unittest.TestCase):
    backend = "sqlite"

    @classmethod
    def setUpClass(cls):
        cls._tmp = None
        if cls.backend == "mysql":
            settings = mysql_test_settings()
            if settings is None:
                raise unittest.SkipTest("MySQL test database not configured (see README).")
            import init_db
            init_db.create_schema(settings)
            cls._settings = settings
        else:
            cls._tmp = tempfile.TemporaryDirectory()
            cls._settings = {"DB_BACKEND": "sqlite",
                             "SQLITE_PATH": os.path.join(cls._tmp.name, "test.sqlite3")}

    @classmethod
    def tearDownClass(cls):
        if cls._tmp is not None:
            cls._tmp.cleanup()

    def setUp(self):
        settings = dict(self._settings, TESTING=True, CSRF_ENABLED=False,
                        SECRET_KEY="test-secret", CURRENCY_SYMBOL="Rs.")
        self.app = create_app(settings)
        self.client = self.app.test_client()
        self.repo = self.app.extensions["expense_repo"]
        self.db = self.app.extensions["expense_db"]
        self._reset_tables()

    def _reset_tables(self):
        if self.backend == "sqlite":
            path = self._settings["SQLITE_PATH"]
            if os.path.exists(path):
                os.remove(path)
            conn = sqlite3.connect(path)
            try:
                conn.executescript((PROJECT_DIR / "tests" / "sqlite_schema.sql")
                                   .read_text(encoding="utf-8"))
                conn.commit()
            finally:
                conn.close()
        else:
            self.db.execute("DELETE FROM expenses")
            self.db.execute("DELETE FROM categories")

    # ---- helpers -----------------------------------------------------------
    def make_category(self, name="Food", description=None):
        return self.repo.create_category(name, description)

    def make_expense(self, category_id, title="Lunch", amount="100.00",
                     when="2026-09-10", notes=None):
        from decimal import Decimal
        return self.repo.create_expense({
            "title": title, "amount": Decimal(str(amount)),
            "expense_date": date.fromisoformat(when),
            "category_id": category_id, "notes": notes})

    def form(self, cid, **overrides):
        data = {"title": "Tea", "amount": "25.50",
                "expense_date": "2026-09-10", "category_id": str(cid),
                "notes": "hot"}
        data.update(overrides)
        return data

    @staticmethod
    def yesterday():
        return (date.today() - timedelta(days=1)).isoformat()
