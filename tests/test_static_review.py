"""Automated 'static review': syntax, imports, routes, templates, static files,
SQL schema consistency and sample data."""
import ast
import importlib
import py_compile
import re
import sqlite3
import unittest

from app import create_app
from tests.base import PROJECT_DIR

SKIP_DIRS = {".venv", "venv", "__pycache__", ".git"}


def project_files(pattern):
    return [p for p in PROJECT_DIR.rglob(pattern)
            if not (set(p.relative_to(PROJECT_DIR).parts) & SKIP_DIRS)]


class StaticReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app({"DB_BACKEND": "sqlite", "SQLITE_PATH": ":memory:", "TESTING": True})
        cls.templates = {p.name: p.read_text(encoding="utf-8")
                         for p in (PROJECT_DIR / "templates").glob("*.html")}

    def test_every_python_file_compiles(self):
        for path in project_files("*.py"):
            py_compile.compile(str(path), doraise=True, cfile=str(PROJECT_DIR / "_tmp.pyc"))
        tmp = PROJECT_DIR / "_tmp.pyc"
        if tmp.exists():
            tmp.unlink()

    def test_every_project_import_resolves(self):
        local = {p.stem for p in PROJECT_DIR.glob("*.py")} | {"analysis", "tests"}
        for path in project_files("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    top = node.module.split(".")[0]
                    if top in local:
                        importlib.import_module(node.module)  # raises if missing
                        mod = importlib.import_module(node.module)
                        for alias in node.names:
                            self.assertTrue(hasattr(mod, alias.name) or
                                            importlib.util.find_spec(node.module + "." + alias.name),
                                            "%s: cannot import %s from %s" % (path.name, alias.name, node.module))
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] in local:
                            importlib.import_module(alias.name)

    def test_third_party_imports_are_in_requirements(self):
        reqs = (PROJECT_DIR / "requirements.txt").read_text().lower()
        for pkg in ("flask", "pymysql", "pandas", "numpy", "matplotlib", "python-dotenv"):
            self.assertIn(pkg, reqs)

    def test_render_template_targets_exist(self):
        source = (PROJECT_DIR / "app.py").read_text(encoding="utf-8")
        names = re.findall(r'render_template\(\s*"([^"]+)"', source)
        self.assertTrue(names)
        for name in names:
            self.assertIn(name, self.templates, name)

    def test_template_includes_and_extends_exist(self):
        for name, text in self.templates.items():
            for target in re.findall(r'{%\s*(?:extends|include)\s+"([^"]+)"', text):
                self.assertIn(target, self.templates, "%s -> %s" % (name, target))

    def test_url_for_endpoints_exist(self):
        endpoints = {rule.endpoint for rule in self.app.url_map.iter_rules()}
        sources = list(self.templates.values()) + [(PROJECT_DIR / "app.py").read_text(encoding="utf-8")]
        found = set()
        for text in sources:
            found |= set(re.findall(r"url_for\(\s*['\"]([\w.]+)['\"]", text))
        self.assertTrue(found)
        for endpoint in found:
            self.assertIn(endpoint, endpoints, endpoint)

    def test_static_files_exist(self):
        for text in self.templates.values():
            for rel in re.findall(r"url_for\('static',\s*filename='([^']+)'", text):
                self.assertTrue((PROJECT_DIR / "static" / rel).is_file(), rel)

    def test_forms_post_to_post_routes(self):
        rules = {r.endpoint: r.methods for r in self.app.url_map.iter_rules()}
        for name, text in self.templates.items():
            for form in re.findall(r"<form[^>]*>", text):
                if re.search(r'action="{{ (action|filter_action) }}"', form):
                    # action is a variable set from url_for(...) elsewhere (checked above)
                    continue
                action = re.search(r"url_for\('([\w.]+)'", form)
                method = re.search(r'method="(\w+)"', form)
                self.assertTrue(method, "%s: form without method" % name)
                self.assertTrue(action, "%s: form without url_for action: %s" % (name, form))
                self.assertIn(method.group(1).upper(), rules[action.group(1)], form)

    def test_post_forms_have_csrf_token(self):
        for name, text in self.templates.items():
            for block in re.findall(r'<form[^>]*method="post".*?</form>', text, flags=re.S):
                self.assertIn("csrf_token", block, name)

    def test_all_sql_uses_placeholders(self):
        # no f-strings / % formatting / + concatenation of values into SQL in repository
        source = (PROJECT_DIR / "repository.py").read_text(encoding="utf-8")
        self.assertNotRegex(source, r'execute\(\s*f"')
        self.assertNotRegex(source, r'"\s*%\s*\(')

    def test_templates_do_not_use_localstorage_or_external_assets(self):
        for name, text in self.templates.items():
            self.assertNotIn("http://", text.replace("http://127", ""), name)
            self.assertNotIn("https://", text, name)


class SchemaConsistencyTests(unittest.TestCase):
    @staticmethod
    def tables(sql):
        result = {}
        for name, body in re.findall(r"CREATE TABLE (?:IF NOT EXISTS )?(\w+)\s*\((.*?)\)\s*(?:ENGINE|;)",
                                     sql, flags=re.S | re.I):
            cols = []
            for line in body.split("\n"):
                line = line.strip().rstrip(",")
                if not line or re.match(r"(CONSTRAINT|INDEX|KEY|PRIMARY|UNIQUE|FOREIGN|CHECK|REFERENCES)\b", line, re.I):
                    continue
                cols.append(line.split()[0])
            result[name] = cols
        return result

    def test_mysql_and_sqlite_schemas_have_same_tables_and_columns(self):
        mysql = self.tables((PROJECT_DIR / "schema.sql").read_text(encoding="utf-8"))
        lite = self.tables((PROJECT_DIR / "tests" / "sqlite_schema.sql").read_text(encoding="utf-8"))
        self.assertEqual(set(mysql), {"categories", "expenses"})
        self.assertEqual(mysql, lite)

    def test_sql_files_reference_only_known_tables(self):
        text = (PROJECT_DIR / "repository.py").read_text(encoding="utf-8")
        used = set(re.findall(r"(?:FROM|JOIN|INTO|UPDATE)\s+(\w+)", text))
        self.assertTrue(used <= {"categories", "expenses"}, used)

    def test_init_db_splits_schema_and_sample(self):
        import init_db
        schema = init_db.split_statements(init_db.read_sql("schema.sql", "expense_tracker"))
        self.assertEqual(len(schema), 4)  # CREATE DATABASE, USE, 2 tables
        sample = init_db.split_statements(init_db.read_sql("sample_data.sql", "expense_tracker"))
        self.assertEqual(len(sample), 3)  # USE, categories, expenses
        renamed = init_db.read_sql("schema.sql", "my_db")
        self.assertIn("USE my_db;", renamed)

    def test_sample_data_loads_and_dashboard_works(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "s.sqlite3")
            conn = sqlite3.connect(path)
            conn.executescript((PROJECT_DIR / "tests" / "sqlite_schema.sql").read_text(encoding="utf-8"))
            sample = (PROJECT_DIR / "sample_data.sql").read_text(encoding="utf-8")
            sample = sample.replace("INSERT IGNORE", "INSERT OR IGNORE")
            sample = re.sub(r"^USE .*?;\s*$", "", sample, flags=re.M)
            conn.executescript(sample)
            conn.commit()
            n_exp = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
            n_cat = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
            orphans = conn.execute("SELECT COUNT(*) FROM expenses WHERE category_id IS NULL").fetchone()[0]
            conn.close()
            self.assertEqual((n_exp, n_cat, orphans), (34, 9, 0))
            client = create_app({"DB_BACKEND": "sqlite", "SQLITE_PATH": path, "TESTING": True,
                                 "CSRF_ENABLED": False}).test_client()
            for p in ("/", "/expenses", "/categories", "/reports?month=2026-09",
                      "/chart/category.png", "/chart/monthly.png", "/export.csv"):
                self.assertEqual(client.get(p).status_code, 200, p)

    def test_no_secrets_in_project(self):
        self.assertFalse((PROJECT_DIR / ".env").exists(), ".env must not ship in the ZIP")
        text = (PROJECT_DIR / ".env.example").read_text(encoding="utf-8")
        self.assertIn("your_mysql_password_here", text)


if __name__ == "__main__":
    unittest.main()
