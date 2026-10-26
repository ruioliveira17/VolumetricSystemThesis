from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
import hashlib
import json
import logging
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import subprocess
import sys
from pathlib import Path
from threading import Lock

from api_auth import get_current_user
from backend.services.update_manager import (
    UpdateValidationError,
    validate_update_package,
    install_update,
)

_update_lock = Lock()

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/updates",
    tags=["Updates"],
)

VERSION_FILE = Path("/home/marques/Tese/version.txt")
RESTART_CONFIG = Path("/home/marques/Tese/restart_config.json")

UPDATE_URL = os.environ.get("QUBIC_UPDATE_URL", "https://update.balancasmarques.com/v1/check")

def parse_version(version: str) -> tuple[int, ...]:
    """
    Converte uma versão numérica, como '1.0.1', numa tupla
    de inteiros para permitir a comparação semântica.
    """
    if not isinstance(version, str) or not re.fullmatch(
        r"\d+(?:\.\d+)*", version.strip()
    ):
        raise ValueError(f"Formato de versão inválido: {version!r}")

    return tuple(int(part) for part in version.strip().split("."))

def get_installed_version() -> str:
    """
    Lê a versão atualmente instalada a partir de version.txt.
    """
    if not VERSION_FILE.is_file():
        raise FileNotFoundError(
            f"Ficheiro de versão não encontrado: {VERSION_FILE}"
        )

    version = VERSION_FILE.read_text(encoding="utf-8").strip()

    # Valida também o formato da versão local.
    parse_version(version)

    return version

@router.post("/validate")
def validate_update(
    current_user=Depends(get_current_user),
):
    """
    Valida o pacote e verifica se contém uma versão superior
    à versão atualmente instalada.
    """
    try:
        result = validate_update_package()

        remote_version = result["manifest"].get("version")
        installed_version = get_installed_version()

        if not remote_version:
            raise UpdateValidationError(
                "O manifesto não contém uma versão válida."
            )

        try:
            remote_version_tuple = parse_version(remote_version)
            installed_version_tuple = parse_version(installed_version)
        except ValueError as exc:
            raise UpdateValidationError(str(exc)) from exc

        # Igualar o número de componentes para comparar, por exemplo,
        # 1.0 com 1.0.0 como versões equivalentes.
        max_length = max(
            len(remote_version_tuple),
            len(installed_version_tuple),
        )

        remote_version_tuple += (0,) * (
            max_length - len(remote_version_tuple)
        )
        installed_version_tuple += (0,) * (
            max_length - len(installed_version_tuple)
        )

        update_available = (
            remote_version_tuple > installed_version_tuple
        )

        return {
            "success": True,
            "valid": result["valid"],
            "update_available": update_available,
            "installed_version": installed_version,
            "update_id": result["manifest"].get("update_id"),
            "version": remote_version,
            "files_count": len(result["files"]),
            "files": result["files"],
        }

    except UpdateValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception("Erro inesperado ao validar a atualização.")

        raise HTTPException(
            status_code=500,
            detail="Erro interno ao validar o pacote de atualização.",
        ) from exc

def get_install_id() -> str:
    """
    Equivalente ao machineIdSync() do node-machine-id no Linux.
    """
    for path in ("/var/lib/dbus/machine-id", "/etc/machine-id"):
        try:
            raw = Path(path).read_text(encoding="utf-8")
        except OSError:
            continue

        machine_id = "".join(raw.split()).lower()

        if machine_id:
            return hashlib.sha256(machine_id.encode("utf-8")).hexdigest()

    raise UpdateValidationError("Não foi possível obter o ID da máquina.")

def fetch_remote_release() -> dict | None:
    """
    Pergunta ao servidor se existe uma versão mais recente.
    Devolve o objeto "release", ou None se não houver atualização.
   """
    params = urllib.parse.urlencode({
        "produto": "qubic",
        "installId": get_install_id(),
        "version": get_installed_version)(),
    })
    url = f"{UPDATE_URL}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            body = resp.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise UpdateValidationError(
            "Não foi possível contactar o servidor de updates."
        ) from exc

    if not body.strip():
        return None

    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise UpdateValidationError(
            "Resposta inválida do servidor de updates."
        ) from exc

    if not isinstance(data, dict):
        raise UpdateValidationError(
            "Resposta inválida do servidor de updates."
        )

    if not data.get("update"):
        return None

    release = data.get("release")

    if not isinstance(release, dict):
        raise UpdateValidationError(
            "Resposta inválida do servidor de updates."
        )

    return release


@router.post("/check/release")
def check_release(
    current_user=Depends(get_current_user),
):
    """
    Pergunta ao servidor se existe uma versão superior
    à versão atualmente instalada.
    """
    try:
        installed_version = get_installed_version()
        release = fetch_remote_release()

        if release is None:
            return {
                "success": True,
                "valid": True,
                "update_available": False,
                "installed_version": installed_version,
            }

        remote_version = release.get("version")

        if not remote_version:
            raise UpdateValidationError(
                "O servidor não devolveu uma versão válida."
            )

        try:
            remote_version_tuple = parse_version(remote_version)
            installed_version_tuple = parse_version(installed_version)
        except ValueError as exc:
            raise UpdateValidationError(str(exc)) from exc

        # Igualar o número de componentes para comparar, por exemplo,
        # 1.0 com 1.0.0 como versões equivalentes.
        max_length = max(
            len(remote_version_tuple),
            len(installed_version_tuple),
        )

        remote_version_tuple += (0,) * (
            max_length - len(remote_version_tuple)
        )
        installed_version_tuple += (0,) * (
            max_length - len(installed_version_tuple)
        )

        update_available = (
            remote_version_tuple > installed_version_tuple
        )

        return {
            "success": True,
            "valid": True,
            "update_available": update_available,
            "installed_version": installed_version,
            "update_id": release.get("artifact", {}).get("id"),
            "version": remote_version,
            "mandatory": release.get("mandatory", False),
        }

    except UpdateValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception("Erro inesperado ao validar a atualização.")

        raise HTTPException(
            status_code=500,
            detail="Erro interno ao validar o pacote de atualização.",
        ) from exc

def start_update_restart_service():
    logger.info("A solicitar arranque do qubic-update-restart.service.")

    try:
        result = subprocess.run(
            [
                "sudo",
                "-n",
                "/usr/bin/systemctl",
                "start",
                "qubic-update-restart.service",
            ],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

        if result.returncode == 0:
            logger.info(
                "Comando de arranque do serviço executado com sucesso."
            )
        else:
            logger.error(
                "Falha ao iniciar o serviço. Código: %s. Erro: %s",
                result.returncode,
                result.stderr.strip(),
            )

    except Exception:
        logger.exception(
            "Erro ao tentar iniciar qubic-update-restart.service."
        )

def write_restart_config(old_pid: int, python_executable: str):
    config = {
        "old_pid": old_pid,
        "python_executable": python_executable,
    }

    temp_config = RESTART_CONFIG.with_suffix(".tmp")

    temp_config.write_text(
        json.dumps(config, indent=4),
        encoding="utf-8",
    )

    temp_config.replace(RESTART_CONFIG)

    logger.info("Configuração de reinício criada.")

@router.post("/install")
def installUpdate(
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
):
    """
    Valida o pacote e instala os ficheiros no diretório de teste.
    """
    if not _update_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=409,
            detail="Já existe uma atualização em curso."
        )

    try:
        # Guardar os dados do processo atual antes da instalação.
        old_pid = os.getpid()
        python_executable = sys.executable

        result = install_update()

        # Preparar a configuração para o supervisor.
        write_restart_config(
            old_pid=old_pid,
            python_executable=python_executable,
        )

        background_tasks.add_task(start_update_restart_service)

        return result

    except UpdateValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Erro inesperado ao instalar a atualização de teste."
        )

        raise HTTPException(
            status_code=500,
            detail="Erro interno ao instalar a atualização de teste.",
        ) from exc
    finally:
        _update_lock.release()