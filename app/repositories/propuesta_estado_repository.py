"""Consultas de persistencia para estados de propuesta."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.propuesta_estado import PropuestaEstado


class PropuestaEstadoRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_name(self, name: str) -> PropuestaEstado | None:
        """Obtiene un estado por su nombre único."""
        statement = select(PropuestaEstado).where(PropuestaEstado.nombre == name)
        return self.db.scalar(statement)
