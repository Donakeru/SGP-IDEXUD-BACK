"""Schemas para cambiar el estado de una propuesta."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProposalStateChangeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    estado_destino: str = Field(
        alias="estadoDestino",
        min_length=1,
        max_length=100,
    )
    # El autor es siempre el usuario autenticado. Los campos extra (por ejemplo un
    # idUsuario que aún envíe el front) se ignoran: no usar extra="forbid".
    motivo: str | None = Field(default=None, max_length=1000)


class ProposalStateChangeResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    uuid_expediente: UUID = Field(alias="uuidExpediente")
    estado_anterior: str = Field(alias="estadoAnterior")
    estado_nuevo: str = Field(alias="estadoNuevo")
    motivo: str | None
    mensaje: str
