"""Create the MySQL database and tables (and optionally load sample data).

Usage (run from the project folder, with the virtual environment active):

    python init_db.py             create the database and tables (safe to repeat)
    python init_db.py --sample    also load fictional sample data (only if no expenses exist)

It reads your MySQL details from the .env file. It never deletes data.
"""
import argparse
import re
import sys
from pathlib import Path

from config import config_as_dict
from db import config_problems

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_NAME = "expense_tracker"


def split_statements(sql_text):
    """Split a simple SQL script into statements (no procedures/DELIMITER)."""
    lines = [ln for ln in sql_text.splitlines() if not ln.strip().startswith("--")]
    return [s.strip() for s in "\n".join(lines).split(";") if s.strip()]


def read_sql(filename, db_name):
    text = (BASE_DIR / filename).read_text(encoding="utf-8")
    if db_name != DEFAULT_DB_NAME:
        text = re.sub(r"\bexpense_tracker\b", db_name, text)
    return text


def connect_server(cfg):
    import pymysql
    return pymysql.connect(host=cfg["DB_HOST"], port=int(cfg["DB_PORT"]),
                           user=cfg["DB_USER"], password=cfg["DB_PASSWORD"],
                           charset="utf8mb4", connect_timeout=5, autocommit=True)


def run_statements(conn, statements):
    with conn.cursor() as cur:
        for stmt in statements:
            cur.execute(stmt)


def create_schema(cfg):
    conn = connect_server(cfg)
    try:
        run_statements(conn, split_statements(read_sql("schema.sql", cfg["DB_NAME"])))
    finally:
        conn.close()


def load_sample(cfg, force=False):
    """Returns True if loaded, False if skipped because data already exists."""
    conn = connect_server(cfg)
    try:
        with conn.cursor() as cur:
            cur.execute("USE `%s`" % cfg["DB_NAME"])
            cur.execute("SELECT COUNT(*) FROM expenses")
            if cur.fetchone()[0] > 0 and not force:
                return False
        run_statements(conn, split_statements(read_sql("sample_data.sql", cfg["DB_NAME"])))
        return True
    finally:
        conn.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Create the expense tracker database.")
    parser.add_argument("--sample", action="store_true", help="also load sample data")
    parser.add_argument("--force", action="store_true",
                        help="load sample data even if expenses already exist")
    args = parser.parse_args(argv)

    cfg = config_as_dict()
    problems = config_problems(cfg)
    if problems:
        print("Cannot continue - fix your .env file first:")
        for p in problems:
            print("  -", p)
        return 1
    try:
        import pymysql  # noqa: F401
    except ImportError:
        print("PyMySQL is not installed. Run: pip install -r requirements.txt")
        return 1
    try:
        create_schema(cfg)
        print("Database '%s' and tables are ready." % cfg["DB_NAME"])
        if args.sample:
            if load_sample(cfg, force=args.force):
                print("Sample data loaded.")
            else:
                print("Expenses already exist, so sample data was NOT loaded "
                      "(use --force to load it anyway).")
    except Exception as exc:  # show a friendly message instead of a long traceback
        code = exc.args[0] if exc.args and isinstance(exc.args[0], int) else None
        print("Could not talk to MySQL:", exc)
        if code == 1045:
            print("Hint: wrong MySQL user name or password in .env.")
        elif code in (2003, 2002):
            print("Hint: MySQL is not running or DB_HOST / DB_PORT is wrong.")
        print("Run: python diagnose.py   for a detailed check.")
        return 1
    print("Next step: python diagnose.py   then   python app.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
