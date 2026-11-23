from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProposalComment(BaseModel):
    """Comentario renderizable por el frontend."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    content: str
    author: str
    created_at: datetime = Field(alias="createdAt")
    category: str
    # Documento relacionado, si el comentario se hizo sobre uno.
    document_uuid: UUID | None = Field(default=None, alias="documentUuid")
    document_name: str | None = Field(default=None, alias="documentName")


class ProposalComments(BaseModel):
    """Página de comentarios ordenada del más reciente al más antiguo."""

    items: list[ProposalComment]
    total: int
    next_cursor: str | None = None
