"""Modelo ORM para tsgp_usuario."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, Identity, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.comentario import Comentario
    from app.models.documento import Documento
    from app.models.historial_estado import HistorialEstado
    from app.models.usuario_rol import UsuarioRol


class Usuario(Base):
    __tablename__ = "tsgp_usuario"

    id_usuario: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    correo: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    es_activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    usuario_roles: Mapped[list[UsuarioRol]] = relationship(back_populates="usuario", cascade="all, delete-orphan", passive_deletes=True)
    historial_estados: Mapped[list[HistorialEstado]] = relationship(back_populates="usuario", passive_deletes=True)
    documentos: Mapped[list[Documento]] = relationship(back_populates="usuario", cascade="all, delete-orphan", passive_deletes=True)
    comentarios: Mapped[list[Comentario]] = relationship(back_populates="usuario", cascade="all, delete-orphan", passive_deletes=True)
