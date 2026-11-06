"""Modelo ORM para tsgp_propuesta_solicitante."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.propuesta import Propuesta


class PropuestaSolicitante(Base):
    __tablename__ = "tsgp_propuesta_solicitante"
    __table_args__ = (
        UniqueConstraint(
            "id_propuesta",
            name="uq_propuesta_solicitante_propuesta",
        ),
        CheckConstraint(
            "privacidad_aceptada = FALSE OR fecha_aceptacion_privacidad IS NOT NULL",
            name="chk_ps_privacidad_fecha",
        ),
    )

    id_propuesta_solicitante: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )
    id_propuesta: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tsgp_propuesta.id_propuesta", ondelete="CASCADE"),
        nullable=False,
    )
    tipo_solicitante: Mapped[str] = mapped_column(Text, nullable=False)
    nombre_organizacion: Mapped[str | None] = mapped_column(Text)
    nit: Mapped[str | None] = mapped_column(Text)
    nombre_contacto: Mapped[str] = mapped_column(Text, nullable=False)
    cargo_contacto: Mapped[str] = mapped_column(Text, nullable=False)
    correo_contacto: Mapped[str] = mapped_column(Text, nullable=False)
    telefono_contacto: Mapped[str] = mapped_column(Text, nullable=False)
    privacidad_aceptada: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    fecha_aceptacion_privacidad: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    propuesta: Mapped[Propuesta] = relationship(back_populates="solicitante")
