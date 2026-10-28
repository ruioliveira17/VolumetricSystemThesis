import asyncio
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, WebSocket, WebSocketDisconnect
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
from threading import Event, Lock, Thread

from api_auth import get_current_user
from backend.services.update_manager import (
    DEFAULT_PACKAGE,
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

UPDATE_URL_CHECK = os.environ.get("QUBIC_UPDATE_URL_CHECK", "https://update.balancasmarques.com/v1/check")
UPDATE_URL_DOWNLOAD = os.environ.get("QUBIC_UPDATE_URL_DOWNLOAD", "https://update.balancasmarques.com/v1/download")
UPDATE_URL_REPORT = os.environ.get("QUBIC_UPDATE_URL_REPORT", "https://update.balancasmarques.com/v1/report")
UPDATE_URL_HEARTBEAT = os.environ.get("QUBIC_UPDATE_URL_HEARTBEAT", "https://update.balancasmarques.com/v1/heartbeat")

UPDATE_PRODUCT = "qubic"

DEFAULT_POLL_SECONDS = 6 * 60 * 60

_stop_event = Event()
_poll_lock = Lock()
_poll_after = DEFAULT_POLL_SECONDS

_latest_lock = Lock()
_latest = {"checked": False, "update_available": False, "release": None}

_loop: asyncio.AbstractEventLoop | None = None
_clients: set[WebSocket] = set()  # só é mexido dentro do event loop

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

def fetch_remote_release() -> tuple[bool, dict | None, int | None]:
    """
    Pergunta ao servidor se existe uma versão mais recente.
    Devolve o objeto "release", ou None se não houver atualização.
   """
    params = urllib.parse.urlencode({
        "produto": UPDATE_PRODUCT,
        "installId": get_install_id(),
        "version": get_installed_version(),
    })
    url = f"{UPDATE_URL_CHECK}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            body = resp.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise UpdateValidationError(
            "Não foi possível contactar o servidor de updates."
        ) from exc

    if not body.strip():
        return False, None, None

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

    poll_after = data.get("pollAfter")

    if isinstance(poll_after, int) and poll_after > 0:
        global _poll_after
        with _poll_lock:
            _poll_after = poll_after

    update_available = data.get("update")

    if not update_available:
        return False, None, poll_after

    release = data.get("release")

    if not isinstance(release, dict):
        raise UpdateValidationError(
            "Resposta inválida do servidor de updates."
        )

    return update_available, release, poll_after

def build_status(update_available: bool, release: dict | None) -> dict:
    if not update_available or release is None:
        return {"update_available": False}

    return {
        "update_available": True,
        "version": release.get("version"),
        "mandatory": release.get("mandatory", False),
        "update_id": release.get("artifact", {}).get("id"),
        "patch_notes": release.get("notes", {}),
    }

@router.get("/check/release")
def check_release():
    """
    Devolve o último estado conhecido (sem token).
    Quem faz o pedido ao servidor de updates é o ciclo em segundo plano.
    """
    with _latest_lock:
        latest = dict(_latest)

    return {
        "success": True,
        "checked": latest["checked"],
        **build_status(latest["update_available"], latest["release"]),
    }

def fetch_download_info() -> dict:
    """
    Pede ao servidor o link assinado do pacote (válido 10 minutos).
    """
    payload = json.dumps({
        "produto": UPDATE_PRODUCT,
        "installId": get_install_id(),
    }).encode("utf-8")

    request = urllib.request.Request(
        UPDATE_URL_DOWNLOAD,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise UpdateValidationError(
            "Não foi possível contactar o servidor de updates."
        ) from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise UpdateValidationError(
            "Resposta inválida do servidor de updates."
        ) from exc

    if not isinstance(data, dict) or not data.get("update"):
        raise UpdateValidationError(
            "O servidor não tem nenhuma atualização para descarregar."
        )

    if not data.get("url") or not data.get("sha256"):
        raise UpdateValidationError(
            "Resposta inválida do servidor de updates."
        )

    return data

@router.post("/download/release")
def download_release(
    current_user=Depends(get_current_user),
):
    """
    Descarrega o pacote para o disco e verifica o SHA-256.
    Só deve ser chamado quando o utilizador confirma a atualização.
    """
    if not _update_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=409,
            detail="Já existe uma atualização em curso.",
        )

    temp_package = DEFAULT_PACKAGE.with_suffix(".tmp")

    try:
        info = fetch_download_info()
        expected_hash = info["sha256"].lower()

        DEFAULT_PACKAGE.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()

        try:
            with urllib.request.urlopen(info["url"], timeout=30) as resp, \
                    temp_package.open("wb") as out:
                while chunk := resp.read(1024 * 1024):
                    digest.update(chunk)
                    out.write(chunk)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise UpdateValidationError(
                "Falha ao descarregar o pacote de atualização."
            ) from exc

        if digest.hexdigest() != expected_hash:
            raise UpdateValidationError(
                "O SHA-256 do pacote descarregado não corresponde."
            )

        temp_package.replace(DEFAULT_PACKAGE)

        return {
            "success": True,
            "version": info.get("version"),
            "sha256": expected_hash,
            "package": str(DEFAULT_PACKAGE),
        }

    except UpdateValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception("Erro inesperado ao descarregar a atualização.")

        raise HTTPException(
            status_code=500,
            detail="Erro interno ao descarregar a atualização.",
        ) from exc

    finally:
        temp_package.unlink(missing_ok=True)
        _update_lock.release()

def send_heartbeat() -> None:
    """
    Indica ao servidor que a instalação está viva (resposta 204).
    """
    payload = json.dumps({
        "produto": UPDATE_PRODUCT,
        "installId": get_install_id(),
        "version": get_installed_version(),
    }).encode("utf-8")

    request = urllib.request.Request(
        UPDATE_URL_HEARTBEAT,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=10):
            pass
    except (urllib.error.URLError, TimeoutError) as exc:
        raise UpdateValidationError(
            "Não foi possível contactar o servidor de updates."
        ) from exc

@router.post("/heartbeat")
def heartbeat(
    current_user=Depends(get_current_user),
):
    try:
        send_heartbeat()
        return {"success": True}
    except UpdateValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Erro inesperado ao enviar o heartbeat.")
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao enviar o heartbeat.",
        ) from exc

async def _broadcast(status: dict) -> None:
    message = {"event": "UPDATE_AVAILABLE", "data": status}
    for ws in list(_clients):
        try:
            await ws.send_json(message)
        except Exception:
            _clients.discard(ws)


def _emit(status: dict) -> None:
    if _loop is not None:
        asyncio.run_coroutine_threadsafe(_broadcast(status), _loop)


@router.websocket("/updates_ws")
async def updates_ws(websocket: WebSocket):
    # Sem token: só expõe se existe update, a versão e as notas.
    await websocket.accept()
    _clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()  # mantém a ligação aberta
    except WebSocketDisconnect:
        pass
    finally:
        _clients.discard(websocket)

def _offered_version() -> str | None:
    with _latest_lock:
        if _latest["update_available"] and _latest["release"]:
            return _latest["release"].get("version")
    return None

def _update_loop() -> None:
    """
    Heartbeat e Check Release no arranque e depois a cada pollAfter.
    """
    while not _stop_event.is_set():
        try:
            update_available, release, _ = fetch_remote_release()

            offered_before = _offered_version()

            with _latest_lock:
                _latest.update({
                    "checked": True,
                    "update_available": bool(update_available),
                    "release": release,
                })

            # Só quando muda: um check que repete o mesmo resultado não é notícia.
            if offered_before != _offered_version():
                _emit(build_status(bool(update_available), release))

        except Exception:
            logger.exception("Falha no check de updates.")

        try:
            send_heartbeat()
        except Exception:
            logger.exception("Falha ao enviar o heartbeat.")

        with _poll_lock:
            wait = _poll_after

        _stop_event.wait(wait)

def start_update_scheduler(loop: asyncio.AbstractEventLoop) -> None:
    global _loop
    _loop = loop
    Thread(target=_update_loop, name="update-loop", daemon=True).start()

def stop_update_scheduler() -> None:
    _stop_event.set()

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