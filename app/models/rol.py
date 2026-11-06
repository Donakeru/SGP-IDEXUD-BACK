"""Modelo ORM para tsgp_rol."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Identity, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.rol_permiso import RolPermiso
    from app.models.usuario_rol import UsuarioRol


class Rol(Base):
    __tablename__ = "tsgp_rol"

    id_rol: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True)
    nombre: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    usuario_roles: Mapped[list[UsuarioRol]] = relationship(back_populates="rol", cascade="all, delete-orphan", passive_deletes=True)
    rol_permisos: Mapped[list[RolPermiso]] = relationship(back_populates="rol", cascade="all, delete-orphan", passive_deletes=True)
