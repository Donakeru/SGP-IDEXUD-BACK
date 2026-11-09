"""Servicio para consultar valores de listas."""

from sqlalchemy.orm import Session

from app.models.lista_valor import ListaValor
from app.repositories import ListaRepository


class ListaService:

    def __init__(self, db: Session) -> None:
        self.lista_repository = ListaRepository(db)

    def get_values(
        self,
        nombre_lista: str,
        only_active: bool = True,
    ) -> list[ListaValor]:
        lista = self.lista_repository.get_by_name(
            nombre_lista,
            only_active=only_active,
        )
        if lista is None:
            raise ValueError(f"No existe la lista '{nombre_lista}'.")

        return [
            valor
            for valor in lista.valores
            if not only_active or valor.es_activo
        ]
