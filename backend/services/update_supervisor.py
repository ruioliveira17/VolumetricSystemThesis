import json
import os
import signal
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path("/home/marques/Tese")
BACKUP = Path("/home/marques/BackupTese.zip")
CONFIG = Path("/home/marques/Tese/restart_config.json")
HEALTH_URL = "http://127.0.0.1:8000/health"

# Permite importar os módulos do projeto quando o script
# é executado diretamente pelo systemd.
sys.path.insert(0, str(ROOT))

from backend.services.logger import logger

def stop_process(pid, timeout=10):
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.25)

    os.kill(pid, signal.SIGKILL)

def start_api(python_executable):
    return subprocess.Popen(
        [python_executable, str(ROOT / "run_api.py")],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )

def wait_for_health(process, timeout=30):
    deadline = time.time() + timeout

    while time.time() < deadline:
        if process.poll() is not None:
            return False

        try:
            with urlopen(HEALTH_URL, timeout=2) as response:
                if response.status == 200:
                    return True
        except (URLError, TimeoutError, OSError):
            pass

        time.sleep(1)

    return False

def rollback():
    if not BACKUP.is_file():
        raise RuntimeError(
            f"Cópia de segurança não encontrada: {BACKUP}"
        )

    logger.info("A restaurar a cópia de segurança: %s", BACKUP)

    with zipfile.ZipFile(BACKUP, "r") as archive:
        # Verificar a integridade do ZIP antes de extrair.
        corrupted_file = archive.testzip()
        if corrupted_file is not None:
            raise RuntimeError(
                f"Ficheiro corrompido no backup: {corrupted_file}"
            )

        # Validar os caminhos antes de extrair.
        for name in archive.namelist():
            relative = Path(name)

            if relative.is_absolute() or ".." in relative.parts:
                raise RuntimeError(
                    f"Caminho inválido no backup: {name}"
                )

        # Restaurar os ficheiros do backup para a raiz do projeto.
        archive.extractall(ROOT)

    logger.info("Cópia de segurança restaurada.")

def main():
    logger.info("[Update Supervisor] Supervisor chamado.")

    config = json.loads(CONFIG.read_text(encoding="utf-8"))

    old_pid = int(config["old_pid"])
    python_executable = config["python_executable"]

    logger.info("A terminar a API antiga (PID %s).", old_pid)
    stop_process(old_pid)

    logger.info("A iniciar a API atualizada.")
    process = start_api(python_executable)

    if wait_for_health(process):
        logger.info("API atualizada responde corretamente.")
        return

    logger.error("Falha no arranque. A iniciar rollback.")
    stop_process(process.pid)

    rollback()

    logger.info("A iniciar novamente a versão anterior.")
    previous_process = start_api(python_executable)

    if not wait_for_health(previous_process):
        logger.critical("A versão anterior também não arrancou corretamente.")
        raise RuntimeError("Falha no arranque após rollback.")

    logger.info("Rollback concluído. API anterior operacional.")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Falha no processo de atualização.")
        sys.exit(1)