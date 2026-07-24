-- Soft-delete for users: deleting a user must not cascade-delete their
-- measurements. Instead of removing the row, we stamp deleted_at so the
-- user_id FK on measurements stays valid and the history is preserved.
-- NULL = active user; a timestamp = soft-deleted.
ALTER TABLE users ADD COLUMN deleted_at TEXT;
