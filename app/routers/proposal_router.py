"""Endpoints relacionados con propuestas."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import ConfigurationError
from app.dependencies import get_db
from app.schemas.propuesta import (
    CreateProposalDto,
    ProposalListResponse,
    ProposalResponse,
    ProposalReviewItem,
)
from app.services.proposal_service import ProposalService

router = APIRouter(prefix="/proposal", tags=["proposal"])


@router.get("/review", response_model=list[ProposalReviewItem])
def review_proposals(
    db: Session = Depends(get_db),
) -> list[ProposalReviewItem]:
    """Devuelve las propuestas con la información para revisión."""
    return ProposalService(db).list_review()


@router.get("/", response_model=ProposalListResponse)
def get_proposals(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ProposalListResponse:
    """Devuelve una página de propuestas para la tabla del frontend."""
    return ProposalService(db).list_proposals(offset=offset, limit=limit)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=ProposalResponse,
)
def create_new_proposal(
    data: Annotated[CreateProposalDto, Depends(CreateProposalDto.as_form)],
    db: Session = Depends(get_db),
) -> ProposalResponse:
    """Registra la propuesta, el solicitante y sus archivos."""
    try:
        propuesta = ProposalService(db).create_proposal(data=data)
    except ConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return ProposalResponse(
        id_propuesta=propuesta.id_propuesta,
        uuid_expediente=propuesta.uuid_expediente,
        id_propuesta_estado=propuesta.id_propuesta_estado,
        nombre=propuesta.nombre,
        justificacion=propuesta.justificacion,
        fecha_inicio=propuesta.fecha_inicio,
        fecha_fin=propuesta.fecha_fin,
        mensaje="Propuesta registrada correctamente.",
    )
