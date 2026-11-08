from pydantic import BaseModel, ConfigDict

class RolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    nombre: str