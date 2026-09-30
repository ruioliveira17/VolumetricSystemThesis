import json
import logging

from db.connection import get_connection, write_lock

logger = logging.getLogger("qubic.config")

LAST_CONFIGURATION = "last_configuration"
LANGUAGE = "language"

# Códigos i18next suportados pelo frontend. Acrescentar aqui quando houver
# mais traduções (o valor guardado é validado contra esta lista).
SUPPORTED_LANGUAGES = ("pt", "en", "es", "fr")
DEFAULT_LANGUAGE = "en"

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

        except Exception:
            logger.exception("Error saving setting '%s'", key)
            raise

        finally:
            conn.close()


def _get_setting(key):
    conn = get_connection()
    try:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        if row is None:
            logger.info("No setting '%s' found in database", key)
            return None
        
        return row["value"]

    except Exception:
        logger.exception("Error retrieving setting '%s' from database", key)
        raise
    
    finally:
        conn.close()


def save_last_configuration(data):
    _set_setting(LAST_CONFIGURATION, json.dumps(data))
    logger.info("Configuration saved successfully")


def get_last_configuration():
    value = _get_setting(LAST_CONFIGURATION)

    if value:
        return json.loads(value)

    return None


def get_language():
    """Língua escolhida na interface. Se não houver (ou for inválida), devolve o default."""
    value = _get_setting(LANGUAGE)

    if value in SUPPORTED_LANGUAGES:
        return value

    logger.info(
        "No valid language found, using default language '%s'",
        DEFAULT_LANGUAGE
    )
    return DEFAULT_LANGUAGE


def save_language(language):
    """Grava a língua escolhida. Levanta ValueError se não for suportada."""
    code = (language or "").strip().lower()
    if code not in SUPPORTED_LANGUAGES:
        logger.error("Unsupported language '%s'", language)
        raise ValueError("Unsupported language: " + str(language))
    _set_setting(LANGUAGE, code)
    logger.info("Language '%s' saved successfully", code)
    return code
