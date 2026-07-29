import base64
import json
import mimetypes

from db.connection import get_connection, write_lock, row_to_dict, rows_to_dicts

def _scalar(value):
    """Só números vão para colunas escalares; None/listas/dicts/bool -> None.
    O SQLite não sabe bindar listas (o caso 'arrays dentro de arrays' do modo Real)."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    return None

def _dim(value, extra, key):
    """Devolve o valor para a coluna escalar. Se vier em lista/aninhado (Real),
    encaminha-o para o extra_json e deixa a coluna a None."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    if value is not None:
        extra.setdefault(key, value)
    return None

def create_measurement(user_id, volume_mode, object_count, total_volume_m, total_volume_cm, weight, objects):
    with write_lock:
        conn = get_connection()
        try:
            cursor = conn.execute(
                "INSERT INTO measurements "
                "(user_id, volume_mode, object_count, total_volume_m, total_volume_cm, weight) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, volume_mode, object_count, _scalar(total_volume_m), _scalar(total_volume_cm), _scalar(weight)),
            )
            measurement_id = cursor.lastrowid

            for obj in objects:
                extra = dict(obj.get("extra") or {})

                x_cm = _dim(obj.get("x_cm"), extra, "x")
                y_cm = _dim(obj.get("y_cm"), extra, "y")
                z_cm = _dim(obj.get("z_cm"), extra, "z")

                conn.execute(
                    "INSERT INTO measurement_objects "
                    "(measurement_id, idx, volume_m, volume_cm, x_cm, y_cm, z_cm, extra_json) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        measurement_id,
                        obj.get("idx"),
                        _scalar(obj.get("volume_m")),
                        _scalar(obj.get("volume_cm")),
                        x_cm,
                        y_cm,
                        z_cm,
                        json.dumps(extra) if extra else None,
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

def _list(where, params):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT m.*, u.username AS username FROM measurements m "
            "JOIN users u ON u.id = m.user_id "
            "WHERE " + where + " ORDER BY m.id DESC",
            params,
        ).fetchall()
        return rows_to_dicts(rows)
    finally:
        conn.close()

def list_measurements(user_id=None):
    """Medições visíveis (as arquivadas ficam de fora)."""
    if user_id is None:
        return _list("m.archived_at IS NULL", ())
    return _list("m.archived_at IS NULL AND m.user_id = ?", (user_id,))

def list_archived_measurements(user_id=None):
    """Medições arquivadas pelo 'apagar todas' (continuam na BD)."""
    if user_id is None:
        return _list("m.archived_at IS NOT NULL", ())
    return _list("m.archived_at IS NOT NULL AND m.user_id = ?", (user_id,))

def image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()

        encoded = base64.b64encode(image_bytes).decode("utf-8")

        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type is None:
            mime_type = "image/png"

        return f"data:{mime_type};base64,{encoded}"

    except FileNotFoundError:
        return None

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

        detected_image = None
        for image in image_rows:
            if image["kind"] == "detectedObjects":
                detected_image = dict(image)
                detected_image["data"] = image_to_base64(detected_image["path"])
                break

        return {
            "measurement": row_to_dict(measurement),
            "objects": objects,
            "images": detected_image,
        }
    finally:
        conn.close()

def archive_measurement(measurement_id):
    """Arquiva uma medição (soft delete): sai da lista mas nada é apagado."""
    with write_lock:
        conn = get_connection()
        try:
            cursor = conn.execute(
                "UPDATE measurements SET archived_at = datetime('now') "
                "WHERE id = ? AND archived_at IS NULL",
                (measurement_id,),
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

def archive_all_measurements(user_id=None):
    """Arquiva todas as medições visíveis. Com user_id, só as desse utilizador.
    Devolve o número de medições arquivadas."""
    with write_lock:
        conn = get_connection()
        try:
            if user_id is None:
                cursor = conn.execute(
                    "UPDATE measurements SET archived_at = datetime('now') "
                    "WHERE archived_at IS NULL"
                )
            else:
                cursor = conn.execute(
                    "UPDATE measurements SET archived_at = datetime('now') "
                    "WHERE archived_at IS NULL AND user_id = ?",
                    (user_id,),
                )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

def restore_measurement(measurement_id):
    """Desarquiva uma medição (volta à lista)."""
    with write_lock:
        conn = get_connection()
        try:
            cursor = conn.execute(
                "UPDATE measurements SET archived_at = NULL "
                "WHERE id = ? AND archived_at IS NOT NULL",
                (measurement_id,),
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

def restore_all_measurements(user_id=None):
    """Desarquiva todas as medições arquivadas. Com user_id, só as desse utilizador."""
    with write_lock:
        conn = get_connection()
        try:
            if user_id is None:
                cursor = conn.execute(
                    "UPDATE measurements SET archived_at = NULL WHERE archived_at IS NOT NULL"
                )
            else:
                cursor = conn.execute(
                    "UPDATE measurements SET archived_at = NULL "
                    "WHERE archived_at IS NOT NULL AND user_id = ?",
                    (user_id,),
                )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

def delete_measurement(measurement_id):
    with write_lock:
        conn = get_connection()
        try:
            conn.execute("DELETE FROM measurement_objects WHERE measurement_id = ?", (measurement_id,))
            conn.execute("DELETE FROM measurement_images WHERE measurement_id = ?", (measurement_id,))
            cursor = conn.execute("DELETE FROM measurements WHERE id = ?", (measurement_id,))
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

def delete_all_measurements(user_id=None):
    """Apaga fisicamente as medições (não tem volta). O 'apagar todas' do
    frontend usa archive_all_measurements; isto fica para uma limpeza real."""
    with write_lock:
        conn = get_connection()
        try:
            if user_id is None:
                conn.execute("DELETE FROM measurement_objects")
                conn.execute("DELETE FROM measurement_images")
                cursor = conn.execute("DELETE FROM measurements")
            else:
                conn.execute(
                    "DELETE FROM measurement_objects WHERE measurement_id IN "
                    "(SELECT id FROM measurements WHERE user_id = ?)",
                    (user_id,),
                )
                conn.execute(
                    "DELETE FROM measurement_images WHERE measurement_id IN "
                    "(SELECT id FROM measurements WHERE user_id = ?)",
                    (user_id,),
                )
                cursor = conn.execute("DELETE FROM measurements WHERE user_id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()