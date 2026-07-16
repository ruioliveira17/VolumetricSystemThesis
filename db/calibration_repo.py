import json

from db.connection import get_connection, write_lock


def save_calibration(data):
    with write_lock:
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO calibration "
                "(id, detection_area, workspace_warning, workspace_depth, "
                " hmin, hmax, smin, smax, vmin, vmax, color, color_rgb, color_slope, "
                " calibration_color_frame_path, calibration_depth_frame_path, updated_at) "
                "VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now')) "
                "ON CONFLICT(id) DO UPDATE SET "
                "  detection_area=excluded.detection_area, "
                "  workspace_warning=excluded.workspace_warning, "
                "  workspace_depth=excluded.workspace_depth, "
                "  hmin=excluded.hmin, hmax=excluded.hmax, smin=excluded.smin, "
                "  smax=excluded.smax, vmin=excluded.vmin, vmax=excluded.vmax, "
                "  color=excluded.color, color_rgb=excluded.color_rgb, color_slope=excluded.color_slope, "
                "  calibration_color_frame_path=excluded.calibration_color_frame_path, "
                "  calibration_depth_frame_path=excluded.calibration_depth_frame_path, "
                "  updated_at=datetime('now')",
                (
                    json.dumps(data.get("detection_area")),
                    json.dumps(data.get("workspace_warning")),
                    data.get("workspace_depth"),
                    data.get("hmin"), data.get("hmax"), data.get("smin"),
                    data.get("smax"), data.get("vmin"), data.get("vmax"),
                    data.get("color"),
                    json.dumps(data.get("colorRGB")),
                    data.get("colorSlope"),
                    data.get("calibrationColorFrame_path"),
                    data.get("calibrationDepthFrame_path"),
                ),
            )
            conn.commit()
        finally:
            conn.close()


def get_calibration():
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM calibration WHERE id = 1").fetchone()
        if row is None:
            return None
        d = dict(row)
        # Devolve no mesmo formato do antigo workspace_calibration.json
        return {
            "detection_area": json.loads(d["detection_area"]) if d["detection_area"] else None,
            "workspace_warning": json.loads(d["workspace_warning"]) if d["workspace_warning"] else None,
            "workspace_depth": d["workspace_depth"],
            "hmin": d["hmin"], "hmax": d["hmax"], "smin": d["smin"],
            "smax": d["smax"], "vmin": d["vmin"], "vmax": d["vmax"],
            "color": d["color"],
            "colorRGB": json.loads(d["color_rgb"]) if d["color_rgb"] else None,
            "colorSlope": d["color_slope"],
            "calibrationColorFrame_path": d["calibration_color_frame_path"],
            "calibrationDepthFrame_path": d["calibration_depth_frame_path"],
        }
    finally:
        conn.close()
