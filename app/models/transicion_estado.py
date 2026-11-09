"""Modelo ORM para tsgp_transicion_estado."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Identity,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.permiso import Permiso
    from app.models.propuesta_estado import PropuestaEstado


class TransicionEstado(Base):
    __tablename__ = "tsgp_transicion_estado"
    __table_args__ = (
        UniqueConstraint("id_estado_origen", "id_estado_destino", name="uq_transicion_origen_destino"),
    )

    id_transicion: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    id_estado_origen: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tsgp_propuesta_estado.id_propuesta_estado", ondelete="RESTRICT"),
        nullable=False,
    )
    id_estado_destino: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tsgp_propuesta_estado.id_propuesta_estado", ondelete="RESTRICT"),
        nullable=False,
    )
    id_permiso: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("tsgp_permiso.id_permiso", ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    estado_origen: Mapped[PropuestaEstado] = relationship(
        foreign_keys=[id_estado_origen], back_populates="transiciones_origen"
    )
    estado_destino: Mapped[PropuestaEstado] = relationship(
        foreign_keys=[id_estado_destino], back_populates="transiciones_destino"
    )
    permiso: Mapped[Permiso | None] = relationship(back_populates="transiciones")
