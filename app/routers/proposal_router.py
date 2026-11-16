"""Endpoints relacionados con propuestas."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.exceptions import ConfigurationError, DocumentNotFoundError
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


@router.get(
    "/documents/{uuid_archivo}",
    response_class=FileResponse,
    responses={status.HTTP_404_NOT_FOUND: {"description": "Documento no encontrado"}},
)
def get_document(
    uuid_archivo: UUID,
    download: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Devuelve el archivo de un documento adjunto.

    Con ``download=false`` se muestra inline, pero solo PDF e imágenes
    (png, jpeg, webp, gif); cualquier otro tipo se envía como descarga.
    """
    try:
        document = ProposalService(db).get_document_file(uuid_archivo)
    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado.",
        ) from exc

    disposition = "inline" if not download and document.inline_allowed else "attachment"
    return FileResponse(
        path=document.path,
        media_type=document.media_type,
        filename=document.filename,
        content_disposition_type=disposition,
        headers={"X-Content-Type-Options": "nosniff"},
    )


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
