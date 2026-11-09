"""Repositorio síncrono de valores de listas."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ListaValor


class ListaValorRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(
        self,
        id_lista_valor: int,
        only_active: bool = True,
    ) -> ListaValor | None:
        statement = select(ListaValor).where(
            ListaValor.id_lista_valor == id_lista_valor
        )
        if only_active:
            statement = statement.where(ListaValor.es_activo.is_(True))
        return self.db.scalar(statement)
