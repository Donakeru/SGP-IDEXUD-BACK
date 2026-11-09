"""Modelo ORM para tsgp_historial_estado."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.propuesta import Propuesta
    from app.models.propuesta_estado import PropuestaEstado
    from app.models.propuesta_solicitante import PropuestaSolicitante
    from app.models.usuario import Usuario


class HistorialEstado(Base):
    __tablename__ = "tsgp_historial_estado"
    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(id_usuario, id_propuesta_solicitante) = 1",
            name="chk_he_autor",
        ),
        Index("idx_historial_solicitante", "id_propuesta_solicitante"),
    )

    id_historial: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    id_propuesta: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tsgp_propuesta.id_propuesta", ondelete="CASCADE"), nullable=False
    )
    id_estado_anterior: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("tsgp_propuesta_estado.id_propuesta_estado", ondelete="RESTRICT"),
    )
    id_estado_nuevo: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tsgp_propuesta_estado.id_propuesta_estado", ondelete="RESTRICT"),
        nullable=False,
    )
    id_usuario: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tsgp_usuario.id_usuario", ondelete="RESTRICT")
    )
    id_propuesta_solicitante: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("tsgp_propuesta_solicitante.id_propuesta_solicitante", ondelete="CASCADE"),
    )
    motivo: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    propuesta: Mapped[Propuesta] = relationship(back_populates="historial_estados")
    estado_anterior: Mapped[PropuestaEstado | None] = relationship(
        foreign_keys=[id_estado_anterior], back_populates="historial_anterior"
    )
    estado_nuevo: Mapped[PropuestaEstado] = relationship(
        foreign_keys=[id_estado_nuevo], back_populates="historial_nuevo"
    )
    usuario: Mapped[Usuario | None] = relationship(back_populates="historial_estados")
    solicitante: Mapped[PropuestaSolicitante | None] = relationship()