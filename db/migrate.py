import os

from db.connection import get_connection, write_lock
from db import users_repo

ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "ruijoliveira2003@gmail.com"
ADMIN_DEFAULT_PASSWORD = "admin"

MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "migrations")


def _applied_versions(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "version TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT (datetime('now')))"
    )
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {row["version"] for row in rows}


def _pending_files(applied):
    if not os.path.isdir(MIGRATIONS_DIR):
        return []
    files = [f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql")]
    return sorted(f for f in files if f not in applied)


def run_migrations(hash_password=None):
    with write_lock:
        conn = get_connection()
        try:
            applied = _applied_versions(conn)
            for filename in _pending_files(applied):
                with open(os.path.join(MIGRATIONS_DIR, filename), "r") as f:
                    conn.executescript(f.read())
                conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (filename,))
                conn.commit()
        finally:
            conn.close()

    _seed_admin(hash_password)


def _seed_admin(hash_password=None):
    if users_repo.get_by_email(ADMIN_EMAIL) is not None:
        return

    if hash_password is None:
        from auth import get_password_hash
        hash_password = get_password_hash

    users_repo.create_user(
        username=ADMIN_USERNAME,
        email=ADMIN_EMAIL,
        password_hash=hash_password(ADMIN_DEFAULT_PASSWORD),
        role="admin",
    )
