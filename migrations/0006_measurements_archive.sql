-- Archive (soft delete) for measurements: the "delete all" action must not
-- destroy the history. Instead of removing the rows we stamp archived_at, so
-- the measurements (and their objects/images) stay in the database and can be
-- restored later.
-- NULL = visible measurement; a timestamp = archived.
ALTER TABLE measurements ADD COLUMN archived_at TEXT;

CREATE INDEX idx_measurements_archived ON measurements(archived_at);
