import json

from db.connection import get_connection, write_lock

LAST_CONFIGURATION = "last_configuration"


def save_last_configuration(data):
    payload = json.dumps(data)
    with write_lock:
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now')) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = datetime('now')",
                (LAST_CONFIGURATION, payload),
            )
            conn.commit()
        finally:
            conn.close()


def get_last_configuration():
    conn = get_connection()
    try:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (LAST_CONFIGURATION,)).fetchone()
        return json.loads(row["value"]) if row else None
    finally:
        conn.close()
