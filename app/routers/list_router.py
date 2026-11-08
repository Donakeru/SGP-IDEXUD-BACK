"""Endpoints para consultar valores de listas."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.lista import ListaValorResponse
from app.services.lista_service import ListaService

router = APIRouter(prefix="/list", tags=["list"])


@router.get(
    "/{list_name}",
    response_model=list[ListaValorResponse],
    responses={404: {"description": "Lista inexistente o desactivada."}},
)
def get_list_by_name(
    list_name: str,
    db: Session = Depends(get_db),
) -> list[ListaValorResponse]:
    try:
        values = ListaService(db).get_values(nombre_lista=list_name)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return [ListaValorResponse.model_validate(value) for value in values]
