"""Modelo ORM para tsgp_propuesta_estado."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, Identity, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.historial_estado import HistorialEstado
    from app.models.propuesta import Propuesta
    from app.models.transicion_estado import TransicionEstado


class PropuestaEstado(Base):
    __tablename__ = "tsgp_propuesta_estado"

    id_propuesta_estado: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    nombre: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    es_final: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    transiciones_origen: Mapped[list[TransicionEstado]] = relationship(
        foreign_keys="[TransicionEstado.id_estado_origen]",
        back_populates="estado_origen",
        passive_deletes=True,
    )
    transiciones_destino: Mapped[list[TransicionEstado]] = relationship(
        foreign_keys="[TransicionEstado.id_estado_destino]",
        back_populates="estado_destino",
        passive_deletes=True,
    )
    propuestas: Mapped[list[Propuesta]] = relationship(back_populates="estado", passive_deletes=True)
    historial_anterior: Mapped[list[HistorialEstado]] = relationship(
        foreign_keys="[HistorialEstado.id_estado_anterior]",
        back_populates="estado_anterior",
        passive_deletes=True,
    )
    historial_nuevo: Mapped[list[HistorialEstado]] = relationship(
        foreign_keys="[HistorialEstado.id_estado_nuevo]",
        back_populates="estado_nuevo",
        passive_deletes=True,
    )
