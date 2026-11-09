"""Repositorio síncrono de listas."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Lista


class ListaRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_name(self, nombre: str, only_active: bool = True) -> Lista | None:
        statement = select(Lista).where(Lista.nombre == nombre)
        if only_active:
            statement = statement.where(Lista.es_activo.is_(True))
        return self.db.scalar(statement)
