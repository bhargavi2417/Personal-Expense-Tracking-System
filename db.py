
"""Database helper supporting MySQL and SQLite."""

import re
import sqlite3
import certifi
from contextlib import contextmanager

PLACEHOLDER_PASSWORD = "your_mysql_password_here"
_DB_NAME_RE = re.compile(r"^[A-Za-z0-9_]{1,64}$")


class DatabaseError(Exception):
    """A database problem with a safe user-facing message."""


class DatabaseUnavailable(DatabaseError):
    """The database cannot be reached or is not configured."""


class IntegrityViolation(DatabaseError):
    """A database rule was violated."""


def config_problems(cfg):
    """Return configuration problems."""
    problems = []

    if not cfg.get("DB_USER"):
        problems.append("DB_USER is missing.")

    password = cfg.get("DB_PASSWORD")

    if password is None or password == "":
        problems.append("DB_PASSWORD is missing.")
    elif password == PLACEHOLDER_PASSWORD:
        problems.append("DB_PASSWORD still has the example value.")

    name = cfg.get("DB_NAME") or ""

    if not _DB_NAME_RE.match(name):
        problems.append(
            "DB_NAME must contain only letters, digits and underscores."
        )

    return problems


def _explain_mysql_error(exc):
    code = (
        exc.args[0]
        if exc.args and isinstance(exc.args[0], int)
        else None
    )

    if code == 1045:
        return "MySQL rejected the username or password. Check DB_USER and DB_PASSWORD."

    if code == 1049:
        return "The database does not exist. Check DB_NAME."

    if code in (2002, 2003, 2005, 2006, 2013):
        return (
            "Cannot reach the database server. Check DB_HOST, DB_PORT, "
            "TLS settings, and database network access."
        )

    if code in (1146, 1054):
        return "Database tables are missing or outdated."

    return "A MySQL error occurred (code %s)." % code


class Database:
    def __init__(self, cfg):
        self.cfg = cfg
        self.backend = cfg.get("DB_BACKEND", "mysql")
        self._mod = None

    def _connect(self):
        if self.backend == "sqlite":
            self._mod = sqlite3
            path = self.cfg.get("SQLITE_PATH")

            if not path:
                raise DatabaseUnavailable(
                    "SQLITE_PATH is not configured."
                )

            conn = sqlite3.connect(path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            return conn

        problems = config_problems(self.cfg)

        if problems:
            raise DatabaseUnavailable(" ".join(problems))

        try:
            import pymysql
            from pymysql.constants import CLIENT
            import certifi
        except ImportError as exc:
            raise DatabaseUnavailable(
                "A required package is missing. Check requirements.txt."
            ) from exc

        self._mod = pymysql

        try:
            return pymysql.connect(
                host=self.cfg.get("DB_HOST", "localhost"),
                port=int(self.cfg.get("DB_PORT", 3306)),
                user=self.cfg["DB_USER"],
                password=self.cfg["DB_PASSWORD"],
                database=self.cfg["DB_NAME"],
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=10,
                client_flag=CLIENT.FOUND_ROWS,
                autocommit=False,

                # Enable TLS and verify the server certificate.
                ssl={"ca": certifi.where()},
            )

        except pymysql.MySQLError as exc:
            raise DatabaseUnavailable(
                _explain_mysql_error(exc)
            ) from exc

    @contextmanager
    def connection(self):
        conn = self._connect()
        try:
            yield conn
        finally:
            conn.close()

    def _prepare(self, sql):
        if self.backend == "sqlite":
            return sql.replace("%s", "?")
        return sql

    def _run(self, sql, params, mode):
        sql = self._prepare(sql)
        params = tuple(params or ())

        with self.connection() as conn:
            cur = conn.cursor()

            try:
                cur.execute(sql, params)

                if mode == "all":
                    return [dict(row) for row in cur.fetchall()]

                if mode == "one":
                    row = cur.fetchone()
                    return dict(row) if row else None

                conn.commit()
                return cur.lastrowid, cur.rowcount

            except self._mod.IntegrityError as exc:
                conn.rollback()
                raise IntegrityViolation(
                    "That change violates a database rule."
                ) from exc

            except self._mod.Error as exc:
                conn.rollback()

                if self.backend == "mysql":
                    raise DatabaseError(
                        _explain_mysql_error(exc)
                    ) from exc

                raise DatabaseError(
                    "Database error: %s" % exc
                ) from exc

            finally:
                cur.close()

    def query_all(self, sql, params=None):
        return self._run(sql, params, "all")

    def query_one(self, sql, params=None):
        return self._run(sql, params, "one")

    def execute(self, sql, params=None):
        """Run INSERT, UPDATE, or DELETE."""
        return self._run(sql, params, "write")

    def check(self):
        """Verify the connection and required tables."""
        counts = {}

        for table in ("categories", "expenses"):
            row = self.query_one(
                "SELECT COUNT(*) AS n FROM %s" % table
            )
            counts[table] = int(row["n"])

        return counts

       
