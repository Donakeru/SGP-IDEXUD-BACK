"""Modelo ORM para tsgp_lista."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, Identity, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.lista_valor import ListaValor


class Lista(Base):
    __tablename__ = "tsgp_lista"

    id_lista: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )
    nombre: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
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

    valores: Mapped[list[ListaValor]] = relationship(
        back_populates="lista",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
