"""Modelo ORM para tsgp_lista_valor."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
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
    from app.models.lista import Lista


class ListaValor(Base):
    __tablename__ = "tsgp_lista_valor"
    __table_args__ = (
        UniqueConstraint(
            "id_lista",
            "valor",
            name="uq_lista_valor_lista_valor",
        ),
    )

    id_lista_valor: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )
    id_lista: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tsgp_lista.id_lista", ondelete="CASCADE"),
        nullable=False,
    )
    valor: Mapped[str] = mapped_column(Text, nullable=False)
    es_activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
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

    lista: Mapped[Lista] = relationship(back_populates="valores")
