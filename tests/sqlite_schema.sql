-- SQLite twin of schema.sql, used ONLY by the automated tests.
CREATE TABLE categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE COLLATE NOCASE,
    description TEXT NULL,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE expenses (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL,
    amount       NUMERIC NOT NULL CHECK (amount > 0),
    expense_date TEXT NOT NULL,
    category_id  INTEGER NOT NULL REFERENCES categories (id) ON DELETE RESTRICT,
    notes        TEXT NULL,
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
