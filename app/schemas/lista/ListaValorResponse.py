"""DTO de respuesta para los valores de una lista."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ListaValorResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id_lista_valor: int
    valor: str
