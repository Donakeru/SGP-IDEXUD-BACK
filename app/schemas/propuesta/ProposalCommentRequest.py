from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import CategoriaComentario


class ProposalCommentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    content: str = Field(min_length=1, max_length=5000)
    category: CategoriaComentario = CategoriaComentario.VISTO_BUENO
    # Documento sobre el que se hace la observación (uuid_archivo), opcional.
    document_uuid: UUID | None = Field(default=None, alias="documentUuid")
    # El autor es siempre el usuario autenticado. Los campos extra (por ejemplo un
    # idUsuario que aún envíe el front) se ignoran: no usar extra="forbid".
