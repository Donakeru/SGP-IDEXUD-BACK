from pydantic import BaseModel, ConfigDict
from app.schemas.rol import RolResponse

class UserResponse(BaseModel):
    nombre: str
    correo: str
    roles: list[RolResponse] = []