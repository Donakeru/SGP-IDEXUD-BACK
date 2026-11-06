"""Modelo ORM para tsgp_comentario."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.propuesta import Propuesta
    from app.models.usuario import Usuario


class Comentario(Base):
    __tablename__ = "tsgp_comentario"

    id_comentario: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    id_propuesta: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tsgp_propuesta.id_propuesta", ondelete="CASCADE"), nullable=False
    )
    id_usuario: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tsgp_usuario.id_usuario", ondelete="CASCADE"), nullable=False
    )
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    propuesta: Mapped[Propuesta] = relationship(back_populates="comentarios")
    usuario: Mapped[Usuario] = relationship(back_populates="comentarios")
