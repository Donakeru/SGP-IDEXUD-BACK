"""Persistencia de metadata de documentos."""

from typing import Any

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
