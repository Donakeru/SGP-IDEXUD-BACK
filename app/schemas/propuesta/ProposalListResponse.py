"""DTOs para el listado paginado de propuestas."""

from datetime import datetime

from pydantic import BaseModel


class ProposalListItem(BaseModel):
    """Fila de propuesta para la tabla del frontend."""

    id_propuesta: int
    nombre: str
    created_at: datetime
    estado: str
    nombre_postulante: str | None


class ProposalListResponse(BaseModel):
    """Página de resultados para carga incremental."""

    items: list[ProposalListItem]
    total: int
    offset: int
    limit: int
