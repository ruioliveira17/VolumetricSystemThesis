CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    volume_mode TEXT NOT NULL,
    object_count INTEGER NOT NULL DEFAULT 0,
    total_volume_m REAL,
    total_volume_cm REAL,
    workspace_depth REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE measurement_objects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    measurement_id INTEGER NOT NULL REFERENCES measurements(id) ON DELETE CASCADE,
    idx INTEGER NOT NULL,
    volume_m REAL,
    volume_cm REAL,
    x_cm REAL,
    y_cm REAL,
    z_cm REAL,
    depth_cm REAL,
    extra_json TEXT
);

CREATE TABLE measurement_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    measurement_id INTEGER NOT NULL REFERENCES measurements(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    path TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_measurements_user ON measurements(user_id);
CREATE INDEX idx_objects_measurement ON measurement_objects(measurement_id);
CREATE INDEX idx_images_measurement ON measurement_images(measurement_id);
