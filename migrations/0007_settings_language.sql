-- Selected interface language, kept in the settings table next to the
-- last_configuration entry. The value is an i18next language code ('pt', 'en').
-- INSERT OR IGNORE so re-running on a database that already has the key
-- (or a language chosen by the user) never overwrites the current choice.
INSERT OR IGNORE INTO settings (key, value) VALUES ('language', 'pt');
