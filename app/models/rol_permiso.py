"""Modelo ORM para tsgp_rol_permiso."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.permiso import Permiso
    from app.models.rol import Rol


class RolPermiso(Base):
    __tablename__ = "tsgp_rol_permiso"

    id_rol: Mapped[int] = mapped_column(BigInteger, ForeignKey("tsgp_rol.id_rol", ondelete="CASCADE"), primary_key=True)
    id_permiso: Mapped[int] = mapped_column(BigInteger, ForeignKey("tsgp_permiso.id_permiso", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    rol: Mapped[Rol] = relationship(back_populates="rol_permisos")
    permiso: Mapped[Permiso] = relationship(back_populates="rol_permisos")
