import unittest

from app import create_app
from db import Database, DatabaseUnavailable, config_problems
from tests.base import AppTestCase


class ConfigErrorTests(unittest.TestCase):
    def mysql_app(self, **overrides):
        cfg = {"DB_BACKEND": "mysql", "TESTING": True, "CSRF_ENABLED": False,
               "DB_USER": "", "DB_PASSWORD": None, "DB_NAME": "expense_tracker"}
        cfg.update(overrides)
        return create_app(cfg).test_client()

    def test_missing_settings_give_clear_page_not_crash(self):
        r = self.mysql_app().get("/")
        self.assertEqual(r.status_code, 503)
        self.assertIn(b"DB_USER is missing", r.data)
        self.assertIn(b"DB_PASSWORD is missing", r.data)

    def test_placeholder_password_detected(self):
        r = self.mysql_app(DB_USER="root", DB_PASSWORD="your_mysql_password_here").get("/expenses")
        self.assertEqual(r.status_code, 503)
        self.assertIn(b"example value", r.data)

    def test_bad_database_name_detected(self):
        problems = config_problems({"DB_USER": "u", "DB_PASSWORD": "p", "DB_NAME": "bad name;"})
        self.assertEqual(len(problems), 1)

    def test_health_reports_error_json(self):
        r = self.mysql_app().get("/health")
        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.get_json()["status"], "error")

    def test_unreachable_mysql_is_explained(self):
        try:
            import pymysql  # noqa: F401
        except ImportError:
            self.skipTest("PyMySQL not installed here")
        r = self.mysql_app(DB_USER="u", DB_PASSWORD="p", DB_HOST="127.0.0.1", DB_PORT=1).get("/")
        self.assertEqual(r.status_code, 503)
        self.assertIn(b"Cannot reach the MySQL server", r.data)

    def test_database_helper_raises_unavailable(self):
        with self.assertRaises(DatabaseUnavailable):
            Database({"DB_BACKEND": "mysql"}).query_all("SELECT 1")


class RuntimeErrorTests(AppTestCase):
    def test_404_page(self):
        r = self.client.get("/no/such/page")
        self.assertEqual(r.status_code, 404)
        self.assertIn(b"Not found", r.data)

    def test_health_ok(self):
        r = self.client.get("/health")
        self.assertEqual(r.get_json(), {"status": "ok", "categories": 0, "expenses": 0})

    def test_csrf_enforced_when_enabled(self):
        app = create_app(dict(self._settings, TESTING=True, CSRF_ENABLED=True, SECRET_KEY="k"))
        client = app.test_client()
        cid = self.make_category("Food")
        r = client.post("/expenses/add", data=self.form(cid))
        self.assertEqual(r.status_code, 400)
        page = client.get("/expenses/add").data.decode()
        token = page.split('name="csrf_token" value="')[1].split('"')[0]
        r = client.post("/expenses/add", data=dict(self.form(cid), csrf_token=token))
        self.assertEqual(r.status_code, 302)

    def test_database_failure_shows_friendly_error(self):
        import os
        os.remove(self._settings["SQLITE_PATH"])  # tables vanish -> SQL error
        r = self.client.get("/expenses")
        self.assertEqual(r.status_code, 500)
        self.assertIn(b"Database problem", r.data)


if __name__ == "__main__":
    unittest.main()
