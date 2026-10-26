
import logging
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from backend.services.update_manager import (
    UpdateValidationError,
    validate_update_package,
    install_test_update,
)

from api_auth import get_current_user


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/updates",
    tags=["Updates"],
)

VERSION_FILE = Path("/home/marques/Tese/version.txt")


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


@router.post("/install-test")
def install_update_test(
    current_user=Depends(get_current_user),
):
    """
    Valida o pacote e instala os ficheiros no diretório de teste.
    """
    try:
        result = install_test_update()
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
