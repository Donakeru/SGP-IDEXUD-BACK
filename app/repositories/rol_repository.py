"""Operaciones de persistencia para tsgp_rol."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Rol


class RolRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(self) -> list[Rol]:
        result = self.db.execute(select(Rol))
        return list(result.scalars().all())

    def get_by_id(self, id_rol: int) -> Rol | None:
        return self.db.get(Rol, id_rol)

    def create(self, data: dict[str, Any]) -> Rol:
        rol = Rol(**data)
        self.db.add(rol)
        try:
            self.db.commit()
            self.db.refresh(rol)
        except Exception:
            self.db.rollback()
            raise
        return rol

    def update(self, id_rol: int, data: dict[str, Any]) -> Rol | None:
        rol = self.get_by_id(id_rol)
        if rol is None:
            return None
        for field, value in data.items():
            if field not in {"id_rol", "created_at", "updated_at"}:
                setattr(rol, field, value)
        rol.updated_at = datetime.now(timezone.utc)
        try:
            self.db.commit()
            self.db.refresh(rol)
        except Exception:
            self.db.rollback()
            raise
        return rol
