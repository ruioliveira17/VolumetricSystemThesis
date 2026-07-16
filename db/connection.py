import os
import sqlite3
import threading

write_lock = threading.Lock()

DEFAULT_DB_PATH = "data/app.db"


def db_path():
    return os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH)


def get_connection():
    path = db_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def row_to_dict(row):
    return dict(row) if row is not None else None


def rows_to_dicts(rows):
    return [dict(row) for row in rows]
