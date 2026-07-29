import json

from db.connection import get_connection, write_lock

LAST_CONFIGURATION = "last_configuration"
LANGUAGE = "language"

# Códigos i18next suportados pelo frontend. Acrescentar aqui quando houver
# mais traduções (o valor guardado é validado contra esta lista).
SUPPORTED_LANGUAGES = ("pt", "en")
DEFAULT_LANGUAGE = "pt"

def _set_setting(key, value):
    with write_lock:
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now')) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = datetime('now')",
                (key, value),
            )
            conn.commit()
        finally:
            conn.close()


def _get_setting(key):
    conn = get_connection()
    try:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None
    finally:
        conn.close()


def save_last_configuration(data):
    _set_setting(LAST_CONFIGURATION, json.dumps(data))


def get_last_configuration():
    value = _get_setting(LAST_CONFIGURATION)
    return json.loads(value) if value else None


def get_language():
    """Língua escolhida na interface. Se não houver (ou for inválida), devolve o default."""
    value = _get_setting(LANGUAGE)
    return value if value in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def save_language(language):
    """Grava a língua escolhida. Levanta ValueError se não for suportada."""
    code = (language or "").strip().lower()
    if code not in SUPPORTED_LANGUAGES:
        raise ValueError("Unsupported language: " + str(language))
    _set_setting(LANGUAGE, code)
    return code
