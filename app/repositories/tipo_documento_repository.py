"""Consultas de tipos documentales."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import TipoDocumento


class TipoDocumentoRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_name(self, name: str) -> TipoDocumento | None:
        statement = select(TipoDocumento).where(TipoDocumento.nombre == name)
        return self.db.scalar(statement)
