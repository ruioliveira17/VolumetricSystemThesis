ALTER TABLE measurements ADD COLUMN weight REAL;
ALTER TABLE measurements DROP COLUMN workspace_depth;

ALTER TABLE measurement_objects DROP COLUMN depth_cm;

CREATE TABLE calibration (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    detection_area TEXT,
    workspace_warning TEXT,
    workspace_depth REAL,
    hmin INTEGER,
    hmax INTEGER,
    smin INTEGER,
    smax INTEGER,
    vmin INTEGER,
    vmax INTEGER,
    color TEXT,
    color_rgb TEXT,
    color_slope INTEGER,
    calibration_color_frame_path TEXT,
    calibration_depth_frame_path TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
