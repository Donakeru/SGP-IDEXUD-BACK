"""Inserción de solicitantes asociados a una propuesta."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models import PropuestaSolicitante


class PropuestaSolicitanteRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, data: dict[str, Any]) -> PropuestaSolicitante:
        """Agrega un solicitante a la sesión sin confirmar la transacción."""
        solicitante = PropuestaSolicitante(**data)

        if (
            solicitante.privacidad_aceptada
            and solicitante.fecha_aceptacion_privacidad is None
        ):
            solicitante.fecha_aceptacion_privacidad = datetime.now(timezone.utc)

        self.db.add(solicitante)
        return solicitante

    def create(self, data: dict[str, Any]) -> PropuestaSolicitante:
        """Inserta un solicitante y devuelve la entidad persistida."""
        solicitante = self.add(data)
        try:
            self.db.commit()
            self.db.refresh(solicitante)
        except Exception:
            self.db.rollback()
            raise
        return solicitante
