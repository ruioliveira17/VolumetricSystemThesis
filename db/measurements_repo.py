import json

from db.connection import get_connection, write_lock, row_to_dict, rows_to_dicts


def create_measurement(user_id, volume_mode, object_count, total_volume_m, total_volume_cm, weight, objects):
    with write_lock:
        conn = get_connection()
        try:
            cursor = conn.execute(
                "INSERT INTO measurements "
                "(user_id, volume_mode, object_count, total_volume_m, total_volume_cm, weight) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, volume_mode, object_count, total_volume_m, total_volume_cm, weight),
            )
            measurement_id = cursor.lastrowid

            for obj in objects:
                extra = obj.get("extra")
                conn.execute(
                    "INSERT INTO measurement_objects "
                    "(measurement_id, idx, volume_m, volume_cm, x_cm, y_cm, z_cm, extra_json) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        measurement_id,
                        obj["idx"],
                        obj.get("volume_m"),
                        obj.get("volume_cm"),
                        obj.get("x_cm"),
                        obj.get("y_cm"),
                        obj.get("z_cm"),
                        json.dumps(extra) if extra is not None else None,
                    ),
                )

            conn.commit()
            return measurement_id
        finally:
            conn.close()


def add_images(measurement_id, images):
    with write_lock:
        conn = get_connection()
        try:
            for image in images:
                conn.execute(
                    "INSERT INTO measurement_images (measurement_id, kind, path) VALUES (?, ?, ?)",
                    (measurement_id, image["kind"], image["path"]),
                )
            conn.commit()
        finally:
            conn.close()


def list_measurements(user_id=None):
    conn = get_connection()
    try:
        if user_id is None:
            rows = conn.execute(
                "SELECT m.*, u.username AS username FROM measurements m "
                "JOIN users u ON u.id = m.user_id ORDER BY m.id DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT m.*, u.username AS username FROM measurements m "
                "JOIN users u ON u.id = m.user_id WHERE m.user_id = ? ORDER BY m.id DESC",
                (user_id,),
            ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()


def get_measurement(measurement_id):
    conn = get_connection()
    try:
        measurement = conn.execute(
            "SELECT * FROM measurements WHERE id = ?", (measurement_id,)
        ).fetchone()
        if measurement is None:
            return None

        object_rows = conn.execute(
            "SELECT * FROM measurement_objects WHERE measurement_id = ? ORDER BY idx",
            (measurement_id,),
        ).fetchall()
        image_rows = conn.execute(
            "SELECT * FROM measurement_images WHERE measurement_id = ? ORDER BY id",
            (measurement_id,),
        ).fetchall()

        objects = []
        for row in object_rows:
            obj = dict(row)
            obj["extra"] = json.loads(obj["extra_json"]) if obj["extra_json"] else None
            objects.append(obj)

        return {
            "measurement": row_to_dict(measurement),
            "objects": objects,
            "images": rows_to_dicts(image_rows),
        }
    finally:
        conn.close()
