"""Operaciones de persistencia de propuestas."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.propuesta import Propuesta


class PropuestaRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, data: dict[str, Any]) -> Propuesta:
        """Agrega una propuesta a la sesión sin confirmar la transacción."""
        propuesta = Propuesta(**data)
        self.db.add(propuesta)
        return propuesta

    def get_page(self, offset: int, limit: int) -> tuple[list[Propuesta], int]:
        """Obtiene una página ordenada y el total de propuestas.

        Las relaciones de estado y solicitante se cargan en la misma consulta
        para evitar consultas adicionales por cada fila de la tabla.
        """
        total = self.db.scalar(select(func.count()).select_from(Propuesta)) or 0

        statement = (
            select(Propuesta)
            .options(
                joinedload(Propuesta.estado),
                joinedload(Propuesta.solicitante),
            )
            .order_by(Propuesta.created_at.desc(), Propuesta.id_propuesta.desc())
            .offset(offset)
            .limit(limit)
        )
        propuestas = list(self.db.scalars(statement).unique().all())

        return propuestas, total
