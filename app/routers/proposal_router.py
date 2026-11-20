"""Endpoints relacionados con propuestas."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConfigurationError,
    DocumentNotFoundError,
    InvalidCommentCursorError,
    InvalidCommentError,
    InvalidDocumentTypeError,
    InvalidDocumentUploaderError,
    InvalidProposalTransitionError,
    InvalidTransitionActorError,
    InvalidUploadError,
    ProposalNotFoundError,
    ProposalStateNotFoundError,
    UnsupportedReviewRoleError,
    UploadTooLargeError,
)
from app.dependencies import get_db
from app.schemas.propuesta import (
    CreateProposalDto,
    ProposalComment,
    ProposalCommentRequest,
    ProposalComments,
    ProposalDetailResponse,
    ProposalDocumentUploadResponse,
    ProposalListResponse,
    ProposalResponse,
    ProposalReviewItem,
    ProposalStateChangeRequest,
    ProposalStateChangeResponse,
)
from app.services.proposal_service import ProposalService

router = APIRouter(prefix="/proposal", tags=["proposal"])


@router.get("/review", response_model=list[ProposalReviewItem])
def review_proposals(
    rol: str = Query(
        ...,
        min_length=1,
        description="Código del rol de la bandeja de revisión.",
    ),
    db: Session = Depends(get_db),
) -> list[ProposalReviewItem]:
    """Devuelve las propuestas filtradas por la bandeja del rol."""
    try:
        return ProposalService(db).list_review(rol=rol)
    except UnsupportedReviewRoleError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/{uuid_expediente}/detail",
    response_model=ProposalDetailResponse,
)
def get_proposal_detail(
    uuid_expediente: UUID,
    db: Session = Depends(get_db),
) -> ProposalDetailResponse:
    """Devuelve el detalle de revisión y los tres comentarios más recientes."""
    try:
        return ProposalService(db).get_proposal_detail(uuid_expediente)
    except ProposalNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propuesta no encontrada.",
        ) from exc


@router.get(
    "/{uuid_expediente}/comments",
    response_model=ProposalComments,
)
def get_proposal_comments(
    uuid_expediente: UUID,
    cursor: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ProposalComments:
    """Devuelve una página de tres comentarios para carga incremental."""
    try:
        return ProposalService(db).list_comments(uuid_expediente, cursor=cursor)
    except ProposalNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propuesta no encontrada.",
        ) from exc
    except InvalidCommentCursorError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/{uuid_expediente}/comments",
    status_code=status.HTTP_201_CREATED,
    response_model=ProposalComment,
)
def create_proposal_comment(
    uuid_expediente: UUID,
    data: ProposalCommentRequest,
    db: Session = Depends(get_db),
) -> ProposalComment:
    """Registra un comentario en la propuesta."""
    try:
        return ProposalService(db).create_comment(
            uuid_expediente=uuid_expediente,
            content=data.content,
            id_usuario=data.id_usuario,
        )
    except ProposalNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propuesta no encontrada.",
        ) from exc
    except InvalidCommentError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/{uuid_expediente}/documents",
    status_code=status.HTTP_201_CREATED,
    response_model=ProposalDocumentUploadResponse,
)
def upload_proposal_document(
    uuid_expediente: UUID,
    file: UploadFile = File(...),
    id_usuario: int = Form(..., alias="idUsuario", gt=0),
    tipo_documento: str = Form(..., alias="tipoDocumento"),
    db: Session = Depends(get_db),
) -> ProposalDocumentUploadResponse:
    """Carga un documento a una propuesta por expediente para un usuario activo."""
    try:
        return ProposalService(db).upload_document(
            uuid_expediente=uuid_expediente,
            upload=file,
            id_usuario=id_usuario,
            tipo_documento=tipo_documento,
        )
    except ProposalNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propuesta no encontrada.",
        ) from exc
    except (InvalidDocumentTypeError, InvalidDocumentUploaderError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except UploadTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        ) from exc
    except InvalidUploadError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{uuid_expediente}/status",
    response_model=ProposalStateChangeResponse,
)
def change_proposal_status(
    uuid_expediente: UUID,
    data: ProposalStateChangeRequest,
    db: Session = Depends(get_db),
) -> ProposalStateChangeResponse:
    """Cambia el estado de una propuesta y registra el historial."""
    try:
        result = ProposalService(db).change_proposal_status(
            uuid_expediente=uuid_expediente,
            estado_destino=data.estado_destino,
            id_usuario=data.id_usuario,
            motivo=data.motivo,
        )
    except ProposalNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propuesta   no encontrada.",
        ) from exc
    except InvalidProposalTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except InvalidTransitionActorError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ProposalStateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return ProposalStateChangeResponse(
        uuid_expediente=result.propuesta.uuid_expediente,
        estado_anterior=result.estado_anterior,
        estado_nuevo=result.estado_nuevo,
        motivo=result.motivo,
        mensaje="Estado de la propuesta actualizado correctamente.",
    )


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
    except UploadTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        ) from exc
    except InvalidUploadError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
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
