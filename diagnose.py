"""Check that everything needed to run the project is in place.

Run from the project folder:   python diagnose.py
"""
import importlib
import sys

from config import BASE_DIR, config_as_dict
from db import Database, DatabaseError, config_problems


def line(ok, text):
    print(("[ OK ] " if ok else "[FAIL] ") + text)
    return ok


def main():
    all_ok = True
    print("Python:", sys.version.split()[0])
    for pkg in ("flask", "pymysql", "pandas", "numpy", "matplotlib", "dotenv"):
        try:
            mod = importlib.import_module(pkg)
            line(True, "%s %s" % (pkg, getattr(mod, "__version__", "")))
        except ImportError:
            all_ok = line(False, "%s is not installed -> pip install -r requirements.txt" % pkg)

    env_file = BASE_DIR / ".env"
    all_ok &= line(env_file.exists(), ".env file found" if env_file.exists()
                   else ".env file missing -> copy .env.example to .env and edit it")

    cfg = config_as_dict()
    problems = config_problems(cfg)
    for p in problems:
        all_ok = line(False, p)
    if not problems:
        line(True, "Settings: user=%s host=%s port=%s database=%s (password hidden)" % (
            cfg["DB_USER"], cfg["DB_HOST"], cfg["DB_PORT"], cfg["DB_NAME"]))
        try:
            counts = Database(cfg).check()
            line(True, "Connected to MySQL")
            line(True, "Table 'categories' exists: %d row(s)" % counts["categories"])
            line(True, "Table 'expenses' exists: %d row(s)" % counts["expenses"])
            if counts["expenses"] == 0:
                print("       (No expenses yet. Load samples with: python init_db.py --sample)")
        except DatabaseError as exc:
            all_ok = line(False, str(exc))
    print()
    print("Everything looks good!" if all_ok else "Some checks failed - fix the [FAIL] lines above.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
