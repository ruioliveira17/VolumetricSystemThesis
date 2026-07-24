from db.connection import get_connection, write_lock, row_to_dict, rows_to_dicts


def get_by_login(login):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE (email = ? OR username = ?) AND deleted_at IS NULL",
            (login, login),
        ).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def get_by_username(username):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def get_by_email(email):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def get_by_id(user_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def create_user(username, email, password_hash, role="user"):
    with write_lock:
        conn = get_connection()
        try:
            cursor = conn.execute(
                "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
                (username, email if email else None, password_hash, role),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()


def list_users():
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, username, email, role, created_at FROM users "
            "WHERE deleted_at IS NULL ORDER BY id"
        ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()


def set_role(user_id, role):
    with write_lock:
        conn = get_connection()
        try:
            cursor = conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()


def delete_user(user_id):
    with write_lock:
        conn = get_connection()
        try:
            cursor = conn.execute(
                "UPDATE users SET deleted_at = datetime('now') "
                "WHERE id = ? AND deleted_at IS NULL",
                (user_id,),
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()
