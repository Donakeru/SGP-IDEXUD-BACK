"""Modelo ORM para tsgp_permiso."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Identity, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.rol_permiso import RolPermiso
    from app.models.transicion_estado import TransicionEstado


class Permiso(Base):
    __tablename__ = "tsgp_permiso"

    id_permiso: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    codigo: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    rol_permisos: Mapped[list[RolPermiso]] = relationship(back_populates="permiso", cascade="all, delete-orphan", passive_deletes=True)
    transiciones: Mapped[list[TransicionEstado]] = relationship(back_populates="permiso", passive_deletes=True)
