"""DTO de respuesta para usuarios."""

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.rol import RolResponse


class UserResponse(BaseModel):
    """Información pública de un usuario y sus roles."""

    model_config = ConfigDict(from_attributes=True)

    id_usuario: int
    nombre: str
    correo: str
    es_activo: bool
    roles: list[RolResponse] = Field(default_factory=list)