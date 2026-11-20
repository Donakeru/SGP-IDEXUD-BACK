from pydantic import BaseModel, ConfigDict, Field


class ProposalCommentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    content: str = Field(min_length=1, max_length=5000)
    id_usuario: int = Field(alias="idUsuario", gt=0)
