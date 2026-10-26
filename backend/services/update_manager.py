import hashlib
import json
import logging
import re
import shutil
import zipfile

from pathlib import Path, PurePosixPath


logger = logging.getLogger(__name__)

# Localização do pacote recebido pela Raspberry Pi.
UPDATE_DIR = Path("/home/marques/UpdateQubic")
DEFAULT_PACKAGE = UPDATE_DIR / "qubic-update.zip"

# Destino exclusivo do primeiro teste.
TEST_INSTALL_DIR = Path("/home/marques/Tese/updated")

SHA256_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")
MAX_MANIFEST_SIZE = 1024 * 1024  # 1 MiB
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MiB


class UpdateValidationError(Exception):
    """Erro de estrutura, integridade ou segurança do pacote."""


def _safe_zip_path(value: str) -> PurePosixPath:
    """Valida um caminho relativo dentro do ZIP."""
    if not isinstance(value, str) or not value:
        raise UpdateValidationError("Caminho vazio ou inválido.")

    path = PurePosixPath(value)

    if (
        path.is_absolute()
        or "\\" in value
        or "\x00" in value
        or any(part in ("", ".", "..") for part in value.split("/"))
        or (path.parts and ":" in path.parts[0])
    ):
        raise UpdateValidationError(f"Caminho inseguro: {value}")

    return path


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_update_package(
    package_path: Path = DEFAULT_PACKAGE,
) -> dict:
    """
    Valida a estrutura do ZIP, o manifesto e o SHA-256
    de cada ficheiro declarado, sem instalar ficheiros.
    """
    package_path = Path(package_path)

    if not package_path.is_file():
        raise UpdateValidationError(
            f"Pacote não encontrado: {package_path}"
        )

    try:
        with zipfile.ZipFile(package_path, "r") as archive:
            entries = archive.infolist()
            names = [entry.filename for entry in entries]

            if len(names) != len(set(names)):
                raise UpdateValidationError(
                    "O ZIP contém nomes de ficheiros duplicados."
                )

            for entry in entries:
                _safe_zip_path(entry.filename.rstrip("/")) \
                    if not entry.is_dir() else None

                # Rejeita entradas que excedam o limite de tamanho.
                if entry.file_size > MAX_FILE_SIZE:
                    raise UpdateValidationError(
                        f"Ficheiro demasiado grande: {entry.filename}"
                    )

                # Rejeita ligações simbólicas no ZIP.
                unix_mode = (entry.external_attr >> 16) & 0o170000
                if unix_mode == 0o120000:
                    raise UpdateValidationError(
                        f"Não são permitidas ligações simbólicas: "
                        f"{entry.filename}"
                    )

            if "manifest.json" not in names:
                raise UpdateValidationError(
                    "O ZIP não contém manifest.json na raiz."
                )

            manifest_info = archive.getinfo("manifest.json")

            if manifest_info.file_size > MAX_MANIFEST_SIZE:
                raise UpdateValidationError(
                    "O manifesto excede o tamanho permitido."
                )

            manifest = json.loads(
                archive.read("manifest.json").decode("utf-8")
            )

            if not isinstance(manifest, dict):
                raise UpdateValidationError(
                    "O manifesto tem de ser um objeto JSON."
                )

            files = manifest.get("files")

            if not isinstance(files, list) or not files:
                raise UpdateValidationError(
                    "O manifesto não contém uma lista de ficheiros válida."
                )

            validated_files = []
            seen_sources = set()
            seen_destinations = set()

            for item in files:
                if not isinstance(item, dict):
                    raise UpdateValidationError(
                        "Entrada de ficheiro inválida no manifesto."
                    )

                source = _safe_zip_path(item.get("source"))
                destination = _safe_zip_path(item.get("destination"))
                expected_hash = item.get("sha256")

                if not isinstance(expected_hash, str) or not SHA256_PATTERN.fullmatch(
                    expected_hash
                ):
                    raise UpdateValidationError(
                        f"SHA-256 inválido para {source}."
                    )

                if source.as_posix() in seen_sources:
                    raise UpdateValidationError(
                        f"Origem duplicada no manifesto: {source}"
                    )

                if destination.as_posix() in seen_destinations:
                    raise UpdateValidationError(
                        f"Destino duplicado no manifesto: {destination}"
                    )

                seen_sources.add(source.as_posix())
                seen_destinations.add(destination.as_posix())

                if source.as_posix() not in names:
                    raise UpdateValidationError(
                        f"Ficheiro declarado não encontrado no ZIP: {source}"
                    )

                info = archive.getinfo(source.as_posix())

                if info.is_dir():
                    raise UpdateValidationError(
                        f"A origem não é um ficheiro: {source}"
                    )

                # A primeira versão só permite destinos de teste.
                if destination.parts[0] != "update-test":
                    raise UpdateValidationError(
                        "Destino não permitido nesta fase de teste: "
                        f"{destination}"
                    )

                content = archive.read(info)
                actual_hash = _sha256(content)

                if actual_hash.lower() != expected_hash.lower():
                    raise UpdateValidationError(
                        f"SHA-256 não corresponde: {source}"
                    )

                validated_files.append({
                    "source": source.as_posix(),
                    "destination": destination.as_posix(),
                    "sha256": actual_hash,
                    "size": len(content),
                })

            return {
                "manifest": manifest,
                "files": validated_files,
                "package": str(package_path),
                "valid": True,
            }

    except UpdateValidationError:
        raise
    except (zipfile.BadZipFile, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise UpdateValidationError(
            f"ZIP ou manifesto inválido: {exc}"
        ) from exc


def install_test_update(
    package_path: Path = DEFAULT_PACKAGE,
    install_root: Path = TEST_INSTALL_DIR,
) -> dict:
    """
    Instala apenas ficheiros declarados sob update-test/,
    dentro do diretório isolado de teste.
    """
    result = validate_update_package(package_path)
    install_root = Path(install_root).resolve()
    install_root.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(package_path, "r") as archive:
        for item in result["files"]:
            relative = PurePosixPath(item["destination"]).relative_to(
                "update-test"
            )

            target = (install_root / Path(*relative.parts)).resolve()

            if not target.is_relative_to(install_root):
                raise UpdateValidationError(
                    f"O destino sai da pasta de teste: {target}"
                )

            target.parent.mkdir(parents=True, exist_ok=True)

            # Revalida o conteúdo imediatamente antes de o escrever.
            content = archive.read(item["source"])
            if _sha256(content).lower() != item["sha256"].lower():
                raise UpdateValidationError(
                    f"O ficheiro mudou após a validação: {item['source']}"
                )

            target.write_bytes(content)
            logger.info("Ficheiro de teste instalado: %s", target)

    return {
        "success": True,
        "installed_files": [
            str(
                (install_root / Path(
                    *PurePosixPath(item["destination"])
                    .relative_to("update-test").parts
                )).resolve()
            )
            for item in result["files"]
        ],
        "update_id": result["manifest"].get("update_id"),
        "version": result["manifest"].get("version"),
    }
