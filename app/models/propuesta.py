"""Modelo ORM para tsgp_propuesta."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, Identity, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.comentario import Comentario
    from app.models.documento import Documento
    from app.models.historial_estado import HistorialEstado
    from app.models.propuesta_estado import PropuestaEstado
    from app.models.propuesta_solicitante import PropuestaSolicitante


class Propuesta(Base):
    __tablename__ = "tsgp_propuesta"
    __table_args__ = (
        UniqueConstraint(
            "uuid_expediente",
            name="uq_propuesta_uuid_expediente",
        ),
    )

    id_propuesta: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    uuid_expediente: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        default=uuid4,
    )
    id_propuesta_estado: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tsgp_propuesta_estado.id_propuesta_estado", ondelete="RESTRICT"),
        nullable=False,
    )
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    fecha_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fecha_fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    estado: Mapped[PropuestaEstado] = relationship(back_populates="propuestas")
    historial_estados: Mapped[list[HistorialEstado]] = relationship(
        back_populates="propuesta", cascade="all, delete-orphan", passive_deletes=True
    )
    documentos: Mapped[list[Documento]] = relationship(
        back_populates="propuesta", cascade="all, delete-orphan", passive_deletes=True
    )
    comentarios: Mapped[list[Comentario]] = relationship(
        back_populates="propuesta", cascade="all, delete-orphan", passive_deletes=True
    )
    solicitante: Mapped[PropuestaSolicitante | None] = relationship(
        back_populates="propuesta",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
