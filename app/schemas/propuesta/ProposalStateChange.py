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
    # En modo keycloak se ignora: el autor es el usuario autenticado.
    # TODO(dev-mode): eliminar el campo junto con el modo dev.
    id_usuario: int | None = Field(default=None, alias="idUsuario", gt=0)
    motivo: str | None = Field(default=None, max_length=1000)


class ProposalStateChangeResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    uuid_expediente: UUID = Field(alias="uuidExpediente")
    estado_anterior: str = Field(alias="estadoAnterior")
    estado_nuevo: str = Field(alias="estadoNuevo")
    motivo: str | None
    mensaje: str
