from pydantic import BaseModel, ConfigDict, Field


class ProposalCommentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    content: str = Field(min_length=1, max_length=5000)
    # En modo keycloak se ignora: el autor es el usuario autenticado.
    # TODO(dev-mode): eliminar el campo junto con el modo dev.
    id_usuario: int | None = Field(default=None, alias="idUsuario", gt=0)
