from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProposalComment(BaseModel):
    """Comentario renderizable por el frontend."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    content: str
    author: str
    created_at: datetime = Field(alias="createdAt")


class ProposalComments(BaseModel):
    """Página de comentarios ordenada del más reciente al más antiguo."""

    items: list[ProposalComment]
    total: int
    next_cursor: str | None = None
