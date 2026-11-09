"""Inserción de solicitantes asociados a una propuesta."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models import HistorialEstado


class HistorialEstadoRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, data: dict[str, Any]) -> HistorialEstado:
        cambio_estado = HistorialEstado(**data)
        self.db.add(cambio_estado)
        return cambio_estado
