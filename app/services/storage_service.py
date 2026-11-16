"""Gestión del almacenamiento local de archivos de expedientes."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import BinaryIO
from uuid import UUID, uuid4

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import DocumentNotFoundError

# Prefijo con el que se guarda ruta_archivo en la base de datos.
STORAGE_PATH_PREFIX = "storages"

MIME_EXTENSIONS = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "text/plain": ".txt",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-powerpoint": ".ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
}

ALLOWED_EXTENSIONS = {
    ".doc",
    ".docx",
    ".gif",
    ".jpeg",
    ".jpg",
    ".pdf",
    ".png",
    ".ppt",
    ".pptx",
    ".txt",
    ".webp",
    ".xls",
    ".xlsx",
}


@dataclass(frozen=True)
class StoredFile:
    """Metadata del archivo guardado en el sistema de archivos."""

    uuid_archivo: UUID
    ruta_archivo: str
    nombre_original: str
    tipo_mime: str
    tamano_bytes: int
    hash_sha256: str
    absolute_path: Path


class StorageService:
    """Guarda archivos usando UUID y devuelve sus metadatos."""

    CHUNK_SIZE = 1024 * 1024

    def __init__(self, storage_root: Path | None = None) -> None:
        self.storage_root = storage_root or settings.storage_root

    def ensure_expedition_directory(self, uuid_expediente: UUID) -> Path:
        """Crea y devuelve la carpeta del expediente."""
        directory = self.storage_root / str(uuid_expediente)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def save_upload(self, upload: UploadFile, uuid_expediente: UUID) -> StoredFile:
        """Guarda un archivo en storages/{uuid_expediente}/{uuid_archivo}."""
        uuid_archivo = uuid4()
        extension = self._resolve_extension(upload)
        stored_name = f"{uuid_archivo}{extension}"
        relative_path = (
            Path(STORAGE_PATH_PREFIX)
            / str(uuid_expediente)
            / stored_name
        )
        expedition_directory = self.ensure_expedition_directory(uuid_expediente)

        final_path = expedition_directory / stored_name
        temporary_path = expedition_directory / f".{uuid_archivo}.tmp"
        original_name = upload.filename or str(uuid_archivo)
        mime_type = upload.content_type or "application/octet-stream"
        file_hash = sha256()
        file_size = 0

        try:
            with temporary_path.open("wb") as target:
                file_size = self._copy_and_hash(upload.file, target, file_hash)
            temporary_path.replace(final_path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

        return StoredFile(
            uuid_archivo=uuid_archivo,
            ruta_archivo=relative_path.as_posix(),
            nombre_original=original_name,
            tipo_mime=mime_type,
            tamano_bytes=file_size,
            hash_sha256=file_hash.hexdigest(),
            absolute_path=final_path,
        )

    def resolve_stored_path(self, ruta_archivo: str) -> Path:
        """Resuelve ruta_archivo dentro de storage_root y verifica que exista.

        ruta_archivo se guarda como ``storages/{uuid_expediente}/{archivo}``;
        el prefijo ``storages`` se descarta y el resto se resuelve contra
        ``storage_root``, para que funcione aunque STORAGE_ROOT sea otra carpeta.

        Lanza DocumentNotFoundError si la ruta sale de storage_root (path
        traversal, rutas absolutas, symlinks) o si el archivo no existe.
        """
        parts = PurePosixPath(ruta_archivo.replace("\\", "/")).parts
        if parts and parts[0] == STORAGE_PATH_PREFIX:
            parts = parts[1:]
        if not parts:
            raise DocumentNotFoundError("Ruta de archivo vacía.")

        try:
            root = self.storage_root.resolve()
            candidate = root.joinpath(*parts).resolve()
            is_inside = candidate != root and candidate.is_relative_to(root)
            is_file = is_inside and candidate.is_file()
        except (OSError, ValueError) as exc:
            raise DocumentNotFoundError("Ruta de archivo inválida.") from exc

        if not is_inside:
            raise DocumentNotFoundError("La ruta queda fuera del almacenamiento.")
        if not is_file:
            raise DocumentNotFoundError("El archivo no existe en el almacenamiento.")
        return candidate

    @staticmethod
    def _resolve_extension(upload: UploadFile) -> str:
        """Obtiene una extensión segura sin usar el nombre original completo."""
        content_type = (upload.content_type or "").lower()
        extension = MIME_EXTENSIONS.get(content_type)
        if extension:
            return extension

        original_extension = Path(upload.filename or "").suffix.lower()
        if original_extension in ALLOWED_EXTENSIONS:
            return original_extension
        return ""

    def delete_files(self, files: list[StoredFile]) -> None:
        """Elimina archivos creados durante una transacción fallida."""
        for stored_file in files:
            stored_file.absolute_path.unlink(missing_ok=True)

        for stored_file in files:
            directory = stored_file.absolute_path.parent
            try:
                directory.rmdir()
            except OSError:
                pass

    def delete_expedition_directory(self, uuid_expediente: UUID) -> None:
        """Elimina la carpeta del expediente si quedó vacía."""
        directory = self.storage_root / str(uuid_expediente)
        try:
            directory.rmdir()
        except OSError:
            pass

    def _copy_and_hash(
        self,
        source: BinaryIO,
        target: BinaryIO,
        file_hash,
    ) -> int:
        total_size = 0
        while chunk := source.read(self.CHUNK_SIZE):
            target.write(chunk)
            file_hash.update(chunk)
            total_size += len(chunk)
        return total_size
