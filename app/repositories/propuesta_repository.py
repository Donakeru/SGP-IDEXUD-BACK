"""Operaciones de persistencia de propuestas."""

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import Documento, HistorialEstado, Propuesta, PropuestaEstado


class PropuestaRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, data: dict[str, Any]) -> Propuesta:
        """Agrega una propuesta a la sesión sin confirmar la transacción."""
        propuesta = Propuesta(**data)
        self.db.add(propuesta)
        return propuesta

    def get_by_uuid_for_update(self, uuid_expediente: UUID) -> Propuesta | None:
        """Obtiene una propuesta y bloquea su fila para una transición."""
        statement = (
            select(Propuesta)
            .where(Propuesta.uuid_expediente == uuid_expediente)
            .with_for_update(of=Propuesta)
        )
        return self.db.scalar(statement)

    def get_page(
        self,
        offset: int,
        limit: int,
        state_name: str | None = None,
    ) -> tuple[list[Propuesta], int]:
        """Obtiene una página ordenada y el total de propuestas.

        Las relaciones de estado y solicitante se cargan en la misma consulta
        para evitar consultas adicionales por cada fila de la tabla.
        """
        state_filter = (
            Propuesta.estado.has(PropuestaEstado.nombre == state_name)
            if state_name is not None
            else None
        )
        count_statement = select(func.count()).select_from(Propuesta)
        if state_filter is not None:
            count_statement = count_statement.where(state_filter)
        total = self.db.scalar(count_statement) or 0

        statement = select(Propuesta).options(
            joinedload(Propuesta.estado),
            joinedload(Propuesta.solicitante),
        )
        if state_filter is not None:
            statement = statement.where(state_filter)

        statement = statement.order_by(
            Propuesta.created_at.desc(),
            Propuesta.id_propuesta.desc(),
        ).offset(offset).limit(limit)
        propuestas = list(self.db.scalars(statement).unique().all())

        return propuestas, total

    def get_all_for_review(
        self,
        state_names: Sequence[str] | None = None,
    ) -> list[Propuesta]:
        """Obtiene propuestas de revisión con sus relaciones precargadas."""
        statement = select(Propuesta)
        if state_names is not None:
            if not state_names:
                return []
            statement = statement.where(
                Propuesta.estado.has(PropuestaEstado.nombre.in_(state_names))
            )

        statement = statement.options(
            joinedload(Propuesta.estado),
            joinedload(Propuesta.solicitante),
            selectinload(Propuesta.documentos).joinedload(Documento.tipo_documento),
            selectinload(Propuesta.historial_estados).joinedload(
                HistorialEstado.estado_anterior
            ),
            selectinload(Propuesta.historial_estados).joinedload(
                HistorialEstado.estado_nuevo
            ),
            selectinload(Propuesta.historial_estados).joinedload(
                HistorialEstado.usuario
            ),
            selectinload(Propuesta.historial_estados).joinedload(
                HistorialEstado.solicitante
            ),
        ).order_by(
            Propuesta.created_at.desc(),
            Propuesta.id_propuesta.desc(),
        )
        return list(self.db.scalars(statement).unique().all())
