"""Persistencia de metadata de documentos."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Documento


class DocumentoRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, data: dict[str, Any]) -> Documento:
        """Agrega metadata documental sin confirmar la transacción."""
        documento = Documento(**data)
        self.db.add(documento)
        return documento

    def get_by_uuid(self, uuid_archivo: UUID) -> Documento | None:
        """Obtiene un documento por su uuid_archivo."""
        statement = select(Documento).where(Documento.uuid_archivo == uuid_archivo)
        return self.db.scalar(statement)
