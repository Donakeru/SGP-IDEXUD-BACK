"""Modelo ORM para tsgp_usuario_rol."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.rol import Rol
    from app.models.usuario import Usuario


class UsuarioRol(Base):
    __tablename__ = "tsgp_usuario_rol"

    id_usuario: Mapped[int] = mapped_column(BigInteger, ForeignKey("tsgp_usuario.id_usuario", ondelete="CASCADE"), primary_key=True)
    id_rol: Mapped[int] = mapped_column(BigInteger, ForeignKey("tsgp_rol.id_rol", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    usuario: Mapped[Usuario] = relationship(back_populates="usuario_roles")
    rol: Mapped[Rol] = relationship(back_populates="usuario_roles")
