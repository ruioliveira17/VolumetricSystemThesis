import hashlib
import json
import logging
import os
import re
import zipfile

from pathlib import Path, PurePosixPath

logger = logging.getLogger("qubic.update")

# Localização do pacote recebido pela Raspberry Pi.
UPDATE_DIR = Path("/home/marques/UpdateQubic")
DEFAULT_PACKAGE = UPDATE_DIR / "qubic-update.zip"

# Destino exclusivo do primeiro teste.
INSTALL_DIR = Path("/home/marques/Tese")

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
                # if destination.parts[0] != "update-test":
                #     raise UpdateValidationError(
                #         "Destino não permitido nesta fase de teste: "
                #         f"{destination}"
                #     )

                # Nesta fase, aceita caminhos relativos declarados no payload.

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

def _create_backup(
    install_root: Path,
    backup_path: Path,
) -> Path:
    """
    Cria e valida um backup ZIP antes de substituir o destino final.

    - Não comprime os ficheiros (ZIP_STORED).
    - Exclui pastas geradas e ligações simbólicas.
    - Preserva o backup anterior caso a criação falhe.
    - Remove o ficheiro temporário se a operação for interrompida.
    """
    import tempfile

    install_root = Path(install_root).resolve()
    backup_path = Path(backup_path).resolve()

    if not install_root.is_dir():
        raise UpdateValidationError(
            f"A pasta de instalação não existe: {install_root}"
        )

    if backup_path.is_relative_to(install_root):
        raise UpdateValidationError(
            "O backup não pode ficar dentro da pasta de instalação."
        )

    backup_path.parent.mkdir(parents=True, exist_ok=True)

    excluded_dirs = {
        ".git",
        "__pycache__",
        "logs",
        "node_modules",
        "venv",
        ".venv",
    }

    excluded_files = {
        ".env",
        ".gitignore",
    }

    temp_path = None

    try:
        # Criar o temporário no mesmo sistema de ficheiros
        # para permitir a substituição atómica no final.
        fd, temp_name = tempfile.mkstemp(
            prefix=f"{backup_path.name}.",
            suffix=".tmp",
            dir=backup_path.parent,
        )
        os.close(fd)
        temp_path = Path(temp_name)

        logger.info("A iniciar backup de %s", install_root)
        logger.info("Destino temporário: %s", temp_path)

        # ZIP_STORED evita a compressão DEFLATE.
        with zipfile.ZipFile(
            temp_path,
            mode="w",
            compression=zipfile.ZIP_STORED,
        ) as archive:

            for root, dirs, files in os.walk(
                install_root,
                followlinks=False,
            ):
                root_path = Path(root)

                # Não entrar em pastas excluídas ou symlinks.
                dirs[:] = [
                    name
                    for name in dirs
                    if name not in excluded_dirs
                    and not (root_path / name).is_symlink()
                ]

                # Excluir ficheiros configurados e symlinks.
                files = [
                    name
                    for name in files
                    if name not in excluded_files
                    and not (root_path / name).is_symlink()
                ]

                # Preservar diretórios vazios.
                if (
                    not dirs
                    and not files
                    and root_path != install_root
                ):
                    archive.write(
                        root_path,
                        arcname=(
                            root_path.relative_to(
                                install_root
                            ).as_posix() + "/"
                        ),
                    )

                for name in files:
                    path = root_path / name

                    if path.is_file() and not path.is_symlink():
                        archive.write(
                            path,
                            arcname=path.relative_to(
                                install_root
                            ).as_posix(),
                            compress_type=zipfile.ZIP_STORED,
                        )

        # O ZIP já está fechado. Agora validar a cópia temporária.
        if not temp_path.is_file() or temp_path.stat().st_size == 0:
            raise UpdateValidationError(
                "O ficheiro temporário do backup está vazio ou não existe."
            )

        with zipfile.ZipFile(temp_path, mode="r") as archive:
            if not archive.namelist():
                raise UpdateValidationError(
                    "O backup ZIP ficou vazio."
                )

            corrupted_file = archive.testzip()

            if corrupted_file is not None:
                raise UpdateValidationError(
                    f"Entrada inválida no backup: {corrupted_file}"
                )

        # Só publicar o backup depois da validação.
        # O backup anterior permanece intacto se algo falhar antes daqui.
        os.replace(temp_path, backup_path)
        temp_path = None

        logger.info(
            "Backup criado e validado: %s (%.2f MB)",
            backup_path,
            backup_path.stat().st_size / (1024 * 1024),
        )

        return backup_path

    except Exception:
        logger.exception(
            "Falha ao criar o backup: %s",
            backup_path,
        )
        raise

    finally:
        # Também é executado quando a operação é interrompida
        # por KeyboardInterrupt (Ctrl+C).
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                logger.exception(
                    "Não foi possível remover o temporário: %s",
                    temp_path,
                )

def install_update(
    package_path: Path = DEFAULT_PACKAGE,
    install_root: Path = INSTALL_DIR,
    backup_path: Path = Path("/home/marques/BackupTese.zip"),
) -> dict:
    """
    Valida o pacote, cria um backup da instalação e instala
    os ficheiros declarados no manifesto.

    O backup é criado antes de qualquer ficheiro ser alterado.
    Ainda não executa rollback automático em caso de falha
    durante a instalação.
    """
    logger.info("[UPDATE DEBUG] A iniciar install_update")

    result = validate_update_package(package_path)
    logger.info("Pacote validado: %s", package_path)

    install_root = Path(install_root).resolve()

    if not install_root.is_dir():
        raise UpdateValidationError(
            f"A pasta de instalação não existe: {install_root}"
        )

    logger.info("Raiz de instalação confirmada: %s", install_root)

    install_root = Path(install_root).resolve()

    if not install_root.is_dir():
        raise UpdateValidationError(
            f"A pasta de instalação não existe: {install_root}"
        )

    # 2. Validar previamente todos os destinos.
    destinations = []

    for item in result["files"]:
        logger.info(
            "[UPDATE DEBUG] A validar destino: %s",
            item["destination"],
        )

        relative = PurePosixPath(item["destination"])

        target = (
            install_root / Path(*relative.parts)
        ).resolve()

        if not target.is_relative_to(install_root):
            raise UpdateValidationError(
                f"O destino sai da pasta de instalação: {target}"
            )

        current = install_root

        for part in relative.parts:
            current = current / part

            if current.is_symlink():
                raise UpdateValidationError(
                    "O destino atravessa uma ligação simbólica: "
                    f"{current}"
                )

        destinations.append((item, target))

        logger.info("Destino validado: %s", target)

    # 3. Criar e verificar o backup antes de instalar.
    logger.info("A iniciar criação do backup: %s", backup_path)

    try:
        backup_created = _create_backup(
            install_root=install_root,
            backup_path=backup_path,
        )
    except Exception:
        logger.exception("Erro durante a criação do backup.")
        raise

    logger.info("Backup criado com sucesso: %s", backup_created)

    # 4. Instalar os ficheiros.
    installed_files = []

    with zipfile.ZipFile(package_path, "r") as archive:
        for item, target in destinations:
            content = archive.read(item["source"])

            # Revalidar o conteúdo imediatamente antes da escrita.
            if _sha256(content).lower() != item["sha256"].lower():
                raise UpdateValidationError(
                    f"SHA-256 não corresponde: {item['source']}"
                )

            logger.info(
                "[UPDATE DEBUG] A escrever: %s",
                target,
            )

            target.parent.mkdir(parents=True, exist_ok=True)

            logger.info("A instalar ficheiro: %s", target)

            target.write_bytes(content)

            logger.info(
                "[UPDATE DEBUG] Escrita concluída: %s",
                target,
            )

            installed_files.append(str(target))
            logger.info("Ficheiro instalado: %s", target)

    version = result["manifest"].get("version")

    if not isinstance(version, str) or not version.strip():
        raise UpdateValidationError(
            "O manifesto não contém uma versão válida."
        )

    version_file = install_root / "version.txt"
    version_file.write_text(version.strip() + "\n", encoding="utf-8")

    logger.info(
        "Versão instalada atualizada para %s em %s",
        version.strip(),
        version_file,
    )

    logger.info(
        "Instalação concluída. Ficheiros instalados: %d",
        len(installed_files),
    )

    return {
        "success": True,
        "backup": str(backup_created),
        "installed_files": installed_files,
        "update_id": result["manifest"].get("update_id"),
        "version": result["manifest"].get("version"),
    }
