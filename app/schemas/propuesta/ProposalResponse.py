"""DTO de respuesta para el registro de una propuesta."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ProposalResponse(BaseModel):

    id_propuesta: int
    uuid_expediente: UUID
    id_propuesta_estado: int
    nombre: str
    justificacion: str
    fecha_inicio: datetime
    fecha_fin: datetime | None
    mensaje: str
