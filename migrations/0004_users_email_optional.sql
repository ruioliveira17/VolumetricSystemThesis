-- Make users.email optional (drop NOT NULL). SQLite has no ALTER COLUMN,
-- so the table is rebuilt following the recommended procedure.
PRAGMA foreign_keys = OFF;

CREATE TABLE users_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT INTO users_new (id, username, email, password_hash, role, created_at)
SELECT id, username, email, password_hash, role, created_at FROM users;

DROP TABLE users;
ALTER TABLE users_new RENAME TO users;

PRAGMA foreign_keys = ON;
