"""Modelo ORM para tsgp_documento."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    CHAR,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import EstadoCarga
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.propuesta import Propuesta
    from app.models.tipo_documento import TipoDocumento
    from app.models.usuario import Usuario


class Documento(Base):
    __tablename__ = "tsgp_documento"
    __table_args__ = (
        UniqueConstraint(
            "uuid_archivo",
            name="uq_documento_uuid_archivo",
        ),
        CheckConstraint(
            (
                "estado_carga IN "
                f"('{EstadoCarga.PENDIENTE.value}', "
                f"'{EstadoCarga.CARGADO.value}', "
                f"'{EstadoCarga.FALLIDO.value}')"
            ),
            name="chk_doc_estado_carga",
        ),
        CheckConstraint(
            "num_nonnulls(id_usuario, id_propuesta_solicitante) = 1",
            name="chk_doc_autor",
        ),
        Index(
            "idx_documento_solicitante",
            "id_propuesta_solicitante",
        ),
    )

    id_documento: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    uuid_archivo: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        default=uuid4,
    )
    id_propuesta: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tsgp_propuesta.id_propuesta", ondelete="CASCADE"), nullable=False
    )
    id_tipo_documento: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tsgp_tipo_documento.id_tipo_documento", ondelete="RESTRICT"),
        nullable=False,
    )
    id_usuario: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("tsgp_usuario.id_usuario", ondelete="CASCADE"),
        nullable=True,
    )
    id_propuesta_solicitante: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "tsgp_propuesta_solicitante.id_propuesta_solicitante",
            ondelete="CASCADE",
            name="fk_doc_solicitante",
        ),
        nullable=True,
    )
    id_documento_origen: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("tsgp_documento.id_documento", ondelete="CASCADE"),
    )
    ruta_archivo: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    nombre_original: Mapped[str] = mapped_column(Text, nullable=False)
    tipo_mime: Mapped[str] = mapped_column(Text, nullable=False)
    tamano_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    hash_sha256: Mapped[str | None] = mapped_column(CHAR(64))
    numero_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    es_vigente: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    estado_carga: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'pendiente'"))
    fecha_carga: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    es_activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    fecha_eliminacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    propuesta: Mapped[Propuesta] = relationship(back_populates="documentos")
    tipo_documento: Mapped[TipoDocumento] = relationship(back_populates="documentos")
    usuario: Mapped[Usuario] = relationship(back_populates="documentos")
    documento_origen: Mapped[Documento | None] = relationship(
        "Documento",
        remote_side="Documento.id_documento",
        foreign_keys=[id_documento_origen],
        back_populates="documentos_derivados",
    )
    documentos_derivados: Mapped[list[Documento]] = relationship(
        "Documento",
        foreign_keys=[id_documento_origen],
        back_populates="documento_origen",
        passive_deletes=True,
    )
