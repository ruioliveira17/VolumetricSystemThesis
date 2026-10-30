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
    install_update,
)
_update_lock = Lock()

logger = logging.getLogger("qubic.update")

router = APIRouter(
    prefix="/updates",
    tags=["Updates"],
)

FRONTEND_DIR = Path("/home/marques/Tese/frontend")
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

_update_state_lock = Lock()

_update_state = {
    "status": "idle",
    "version": None,
    "error": None,
}

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

def get_install_id() -> str:
    """
    Obtém o MAC address da interface Ethernet eth0
    e gera um identificador SHA-256.
    """
    try:
        mac_address = Path(
            "/sys/class/net/eth0/address"
        ).read_text().strip().lower()

        mac_address = mac_address.replace(":", "").replace("-", "")

        if len(mac_address) != 12 or not all(
            c in "0123456789abcdef" for c in mac_address
        ):
            raise ValueError("MAC address inválido.")

        return hashlib.sha256(
            mac_address.encode("utf-8")
        ).hexdigest()

    except (OSError, ValueError) as e:
        raise UpdateValidationError(
            "Não foi possível obter o MAC address da interface eth0."
        ) from e

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
        print("UPDATE CHECK ERROR:", repr(exc), "| URL:", url)
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

async def _broadcast(event: str, data: dict) -> None:
    message = {"event": event, "data": data}
    for ws in list(_clients):
        try:
            await ws.send_json(message)
        except Exception:
            _clients.discard(ws)

def _emit(event: str, data: dict) -> None:
    if _loop is not None:
        asyncio.run_coroutine_threadsafe(
            _broadcast(event, data),
            _loop,
        )

def _set_update_state(
    status: str,
    version: str | None = None,
    error: str | None = None,
) -> None:
    with _update_state_lock:
        _update_state.update({
            "status": status,
            "version": version,
            "error": error,
        })

        state = dict(_update_state)

    _emit("UPDATE_STATE", state)

def send_update_report(
    event: str,
    version_from: str | None = None,
    version_to: str | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
) -> None:
    payload = {
        "produto": UPDATE_PRODUCT,
        "installId": get_install_id(),
        "event": event,
    }

    if version_from:
        payload["versionFrom"] = version_from

    if version_to:
        payload["versionTo"] = version_to

    if error_code:
        payload["errorCode"] = error_code

    if error_message:
        payload["errorMessage"] = error_message[:1000]

    request = urllib.request.Request(
        UPDATE_URL_REPORT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            logger.info(
                "Report de atualização enviado: %s (HTTP %s).",
                event,
                response.status,
            )

    except Exception:
        logger.exception(
            "Não foi possível enviar o report %s ao servidor de updates.",
            event,
        )

@router.websocket("/updates_ws")
async def updates_ws(websocket: WebSocket):
    await websocket.accept()
    _clients.add(websocket)

    try:
        with _update_state_lock:
            state = dict(_update_state)

        await websocket.send_json({
            "event": "UPDATE_STATE",
            "data": state,
        })

        while True:
            await websocket.receive_text()

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
                _emit(
                    "UPDATE_AVAILABLE",
                    build_status(
                        bool(update_available),
                        release,
                    ),
                )

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

def _download_release_package() -> dict:
    """
    Descarrega o pacote de atualização e verifica o SHA-256.
    O lock deve estar adquirido pelo endpoint que chama esta função.
    """
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

    finally:
        temp_package.unlink(missing_ok=True)

def _start_restart_and_release_lock() -> None:
    """
    Executa o pedido de reinício depois de a resposta HTTP ser enviada.
    O lock permanece adquirido até esta tarefa começar e terminar.
    """
    try:
        start_update_restart_service()
    finally:
        _update_lock.release()

@router.post("/start_update")
def start_update(
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
):
    """
    Coordena o download, a instalação, a compilação e a preparação
    do reinício do serviço.
    """
    if not _update_lock.acquire(blocking=False):
        raise HTTPException(
            status_code=409,
            detail="Já existe uma atualização em curso.",
        )

    lock_transferred = False

    report_event = "install_fail"
    report_error_code = None
    report_error_message = None
    version_from = None
    version_to = None
    stage = "DOWNLOAD"

    try:
        # 1. Guardar os dados do processo atual.
        old_pid = os.getpid()
        python_executable = sys.executable

        version_from = get_installed_version()
        
        _set_update_state("downloading")
        stage = "DOWNLOAD"
        _emit("UPDATE_STARTED", {})

        # 2. Descarregar o pacote e verificar o SHA-256.
        download_result = _download_release_package()

        # 3. Validar, criar backup e instalar sem atualizar
        #    ainda o ficheiro da versão.
        _set_update_state("installing")
        stage = "INSTALL"

        install_result = install_update(update_version=False)

        # 4. Compilar o frontend com a nova versão do código.
        _set_update_state("building")
        stage = "BUILD"

        try:
            build_result = subprocess.run(
                ["npm", "run", "build"],
                cwd=FRONTEND_DIR,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            logger.exception("Timeout durante a compilação do frontend.")
            raise HTTPException(
                status_code=500,
                detail="A compilação do frontend excedeu o tempo limite.",
            ) from exc
        except OSError as exc:
            logger.exception("Não foi possível executar o build do frontend.")
            raise HTTPException(
                status_code=500,
                detail="Não foi possível executar npm run build.",
            ) from exc

        if build_result.returncode != 0:
            logger.error(
                "Falha no build do frontend. Código: %s\nSTDOUT:\n%s\nSTDERR:\n%s",
                build_result.returncode,
                build_result.stdout[-4000:],
                build_result.stderr[-4000:],
            )
            raise HTTPException(
                status_code=500,
                detail="A compilação do frontend falhou. Consulte os logs.",
            )

        # 5. Só depois de um build bem-sucedido atualizar a versão.
        version = install_result["version"]

        if not isinstance(version, str) or not version.strip():
            raise UpdateValidationError(
                "O manifesto não contém uma versão válida."
            )

        VERSION_FILE.write_text(
            version.strip() + "\n",
            encoding="utf-8",
        )

        version_to = version.strip()

        report_event = "install_ok"
        report_error_code = None
        report_error_message = None

        # 6. Preparar o reinício.
        write_restart_config(
            old_pid=old_pid,
            python_executable=python_executable,
        )

        _emit("FORCE_LOGOUT", {})

        # O BackgroundTask corre depois de a resposta ser enviada.
        # Transfere-lhe a responsabilidade de libertar o lock.
        background_tasks.add_task(_start_restart_and_release_lock)
        lock_transferred = True

        return {
            "success": True,
            "download": download_result,
            "installation": install_result,
            "build": "success",
            "version": version,
            "restart_scheduled": True,
        }

    except HTTPException as exc:
        report_event = "install_fail"
        report_error_code = stage
        report_error_message = str(exc.detail)
        _set_update_state(
            "failed",
            version=version_to or version_from,
            error=report_error_message,
        )
        raise

    except UpdateValidationError as exc:
        report_event = "install_fail"
        report_error_code = "CHECKSUM" if "SHA-256" in str(exc) else stage
        report_error_message = str(exc)
        _set_update_state(
            "failed",
            version=version_to or version_from,
            error=report_error_message,
        )
        raise HTTPException(400, detail=str(exc)) from exc

    except Exception as exc:
        report_event = "install_fail"
        report_error_code = stage
        report_error_message = str(exc)
        logger.exception("Erro inesperado durante a atualização.")
        _set_update_state(
            "failed",
            version=version_to or version_from,
            error=report_error_message,
        )
        raise HTTPException(500, detail="Erro interno durante a atualização.") from exc

    finally:
        try:
            send_update_report(
                event=report_event,
                version_from=version_from,
                version_to=version_to,
                error_code=report_error_code,
                error_message=report_error_message,
            )
        except Exception:
            logger.exception("Erro ao preparar o report da atualização.")

        if not lock_transferred:
            _update_lock.release()