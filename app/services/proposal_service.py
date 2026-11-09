"""Servicio para registrar propuestas, solicitantes y documentos."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.constants import (
    AUTOR_SISTEMA,
    MOTIVO_REGISTRO_INICIAL,
    EstadoCarga,
    EstadoPropuestaNombre,
    HistoryKind,
    TipoDocumentoNombre,
)
from app.core.exceptions import ConfigurationError
from app.models.documento import Documento
from app.models.propuesta import Propuesta
from app.models.tipo_documento import TipoDocumento
from app.repositories import (
    DocumentoRepository,
    HistorialEstadoRepository,
    PropuestaEstadoRepository,
    PropuestaRepository,
    PropuestaSolicitanteRepository,
    TipoDocumentoRepository,
)
from app.schemas.propuesta import (
    CreateProposalDto,
    ProposalListItem,
    ProposalListResponse,
    ProposalReviewDocument,
    ProposalReviewHistory,
    ProposalReviewItem,
)
from app.services.storage_service import StorageService, StoredFile
from app.utils import (
    as_utc_datetime,
    format_date,
    format_file_size,
    format_history_date,
)


class ProposalService:
    """Coordina el registro transaccional de una propuesta."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.propuesta_repository = PropuestaRepository(db)
        self.historial_estado_repository = HistorialEstadoRepository(db)
        self.estado_repository = PropuestaEstadoRepository(db)
        self.solicitante_repository = PropuestaSolicitanteRepository(db)
        self.documento_repository = DocumentoRepository(db)
        self.tipo_documento_repository = TipoDocumentoRepository(db)
        self.storage_service = StorageService()

    def list_proposals(self, offset: int, limit: int) -> ProposalListResponse:
        """Devuelve una página de propuestas para la tabla del frontend."""
        proposals, total = self.propuesta_repository.get_page(
            offset=offset,
            limit=limit,
        )

        items = [
            ProposalListItem(
                id_propuesta=propuesta.id_propuesta,
                nombre=propuesta.nombre,
                created_at=propuesta.created_at,
                estado=propuesta.estado.nombre,
                nombre_postulante=(
                    propuesta.solicitante.nombre_contacto
                    if propuesta.solicitante is not None
                    else None
                ),
            )
            for propuesta in proposals
        ]

        return ProposalListResponse(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
        )

    def create_proposal(self, data: CreateProposalDto) -> Propuesta:
        """Registra propuesta, solicitante y archivos en una transacción.

        Los datos ``proposal_type`` todavía no se guardan porque la tabla de
        propuestas aún no tiene una columna para ese valor.
        """
        estado = self.estado_repository.get_by_name(
            EstadoPropuestaNombre.REGISTRADO.value
        )
        if estado is None:
            raise ConfigurationError(
                f"No existe el estado inicial '{EstadoPropuestaNombre.REGISTRADO.value}' "
                "en la base de datos."
            )

        proposal_document_type = self._get_document_type(
            TipoDocumentoNombre.PROPUESTA
        )
        faculty_document_type = self._get_document_type(TipoDocumentoNombre.FACULTAD)

        propuesta = self.propuesta_repository.create(
            {
                "id_propuesta_estado": estado.id_propuesta_estado,
                "nombre": data.title,
                "descripcion": data.description,
                "justificacion": data.justification,
                "fecha_inicio": as_utc_datetime(data.start_date),
            }
        )

        stored_files: list[StoredFile] = []
        uuid_expediente: UUID | None = None

        try:
            self.db.flush()
            uuid_expediente = propuesta.uuid_expediente

            self.storage_service.ensure_expedition_directory(uuid_expediente)

            solicitante = self.solicitante_repository.add(
                {
                    "id_propuesta": propuesta.id_propuesta,
                    "tipo_solicitante": data.applicant_type,
                    "nombre_organizacion": data.organization_name,
                    "nit": data.nit,
                    "nombre_contacto": data.contact_name,
                    "cargo_contacto": data.contact_role,
                    "correo_contacto": data.email,
                    "telefono_contacto": data.phone,
                    "privacidad_aceptada": data.privacy_accepted,
                }
            )

            self.db.flush()

            self.historial_estado_repository.add(
                {
                    "id_propuesta": propuesta.id_propuesta,
                    "id_estado_anterior": None,
                    "id_estado_nuevo": estado.id_propuesta_estado,
                    "id_propuesta_solicitante": solicitante.id_propuesta_solicitante,
                    "motivo": MOTIVO_REGISTRO_INICIAL,
                }
            )

            self._register_files(
                files=data.proposal_files,
                stored_files=stored_files,
                uuid_expediente=uuid_expediente,
                id_propuesta=propuesta.id_propuesta,
                id_propuesta_solicitante=solicitante.id_propuesta_solicitante,
                tipo_documento=proposal_document_type,
            )
            self._register_files(
                files=data.faculty_files,
                stored_files=stored_files,
                uuid_expediente=uuid_expediente,
                id_propuesta=propuesta.id_propuesta,
                id_propuesta_solicitante=solicitante.id_propuesta_solicitante,
                tipo_documento=faculty_document_type,
            )

            self.db.commit()
        except Exception:
            self.db.rollback()
            self.storage_service.delete_files(stored_files)
            if uuid_expediente is not None:
                self.storage_service.delete_expedition_directory(uuid_expediente)
            raise

        return propuesta

    def _get_document_type(self, name: TipoDocumentoNombre) -> TipoDocumento:
        tipo = self.tipo_documento_repository.get_by_name(name.value)
        if tipo is None:
            raise ConfigurationError(
                f"No existe el tipo de documento '{name.value}' en la base de datos."
            )
        return tipo

    def _register_files(
        self,
        files: list[UploadFile],
        stored_files: list[StoredFile],
        uuid_expediente: UUID,
        id_propuesta: int,
        id_propuesta_solicitante: int,
        tipo_documento: TipoDocumento,
    ) -> None:
        for upload in files:
            stored_file = self.storage_service.save_upload(
                upload=upload,
                uuid_expediente=uuid_expediente,
            )
            stored_files.append(stored_file)

            self.documento_repository.add(
                {
                    "uuid_archivo": stored_file.uuid_archivo,
                    "id_propuesta": id_propuesta,
                    "id_tipo_documento": tipo_documento.id_tipo_documento,
                    "id_propuesta_solicitante": id_propuesta_solicitante,
                    "ruta_archivo": stored_file.ruta_archivo,
                    "nombre_original": stored_file.nombre_original,
                    "tipo_mime": stored_file.tipo_mime,
                    "tamano_bytes": stored_file.tamano_bytes,
                    "hash_sha256": stored_file.hash_sha256,
                    "estado_carga": EstadoCarga.CARGADO.value,
                    "fecha_carga": datetime.now(timezone.utc),
                }
            )

    def list_review(self) -> list[ProposalReviewItem]:
        """Devuelve las propuestas con la información de la vista de revisión."""
        proposals = self.propuesta_repository.get_all_for_review()
        return [self._to_review_item(proposal) for proposal in proposals]

    def _to_review_item(self, propuesta: Propuesta) -> ProposalReviewItem:
        solicitante = propuesta.solicitante
        documents = [
            document
            for document in propuesta.documentos
            if self._is_visible_document(document)
        ]
        proposal_documents = [
            document
            for document in documents
            if document.tipo_documento.nombre == TipoDocumentoNombre.PROPUESTA.value
        ]
        faculty_documents = [
            document
            for document in documents
            if document.tipo_documento.nombre == TipoDocumentoNombre.FACULTAD.value
        ]

        return ProposalReviewItem(
            id=str(propuesta.id_propuesta),
            title=propuesta.nombre,
            entity=solicitante.nombre_organizacion if solicitante else None,
            applicantType=solicitante.tipo_solicitante if solicitante else None,
            contactName=solicitante.nombre_contacto if solicitante else None,
            contactEmail=solicitante.correo_contacto if solicitante else None,
            # proposal_type todavía no se persiste en tsgp_propuesta.
            proposalType=None,
            description=propuesta.descripcion,
            submittedAt=format_date(propuesta.created_at),
            status=propuesta.estado.nombre,
            dataComplete=self._is_data_complete(
                propuesta=propuesta,
                solicitante=solicitante,
                proposal_documents=proposal_documents,
            ),
            # Representa la existencia de un documento de facultad cargado.
            hasFacultyApproval=bool(faculty_documents),
            documents=[
                ProposalReviewDocument(
                    name=document.nombre_original,
                    size=format_file_size(document.tamano_bytes),
                )
                for document in documents
            ],
            history=self._build_history(propuesta),
        )

    @staticmethod
    def _is_visible_document(document: Documento) -> bool:
        return (
            document.es_activo
            and document.es_vigente
            and document.fecha_eliminacion is None
            and document.estado_carga == EstadoCarga.CARGADO.value
        )

    @staticmethod
    def _is_data_complete(
        propuesta: Propuesta,
        solicitante,
        proposal_documents,
    ) -> bool:
        if solicitante is None:
            return False

        required_values = (
            propuesta.nombre,
            propuesta.descripcion,
            propuesta.justificacion,
            propuesta.fecha_inicio,
            solicitante.tipo_solicitante,
            solicitante.nombre_contacto,
            solicitante.correo_contacto,
            solicitante.telefono_contacto,
        )
        return all(value is not None and value != "" for value in required_values) and bool(
            proposal_documents
        )

    def _build_history(self, propuesta: Propuesta) -> list[ProposalReviewHistory]:
        history = sorted(
            propuesta.historial_estados,
            key=lambda item: (item.created_at, item.id_historial),
        )

        return [
            ProposalReviewHistory(
                id=self._history_id(propuesta.id_propuesta, item.id_historial),
                kind=HistoryKind.DECISION.value,
                text=self._history_text(item),
                author=self._history_author(item),
                date=format_history_date(item.created_at),
            )
            for item in history
        ]

    @staticmethod
    def _history_id(id_propuesta: int, id_historial: int) -> str:
        return f"h-{id_propuesta}-{id_historial}"

    @staticmethod
    def _history_author(item) -> str:
        if item.usuario is not None:
            return item.usuario.nombre
        if item.solicitante is not None:
            return item.solicitante.nombre_contacto
        return AUTOR_SISTEMA

    @staticmethod
    def _history_text(item) -> str:
        if item.motivo:
            return item.motivo
        if item.estado_anterior is None:
            return f'Propuesta registrada en estado "{item.estado_nuevo.nombre}".'
        return (
            f'Propuesta cambió de "{item.estado_anterior.nombre}" '
            f'a "{item.estado_nuevo.nombre}".'
        )
