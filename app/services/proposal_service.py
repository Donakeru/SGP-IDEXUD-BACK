"""Servicio para registrar propuestas, solicitantes y documentos."""

from datetime import datetime, timezone

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.propuesta import Propuesta

from app.repositories import (
    DocumentoRepository,
    PropuestaEstadoRepository,
    PropuestaRepository,
    PropuestaSolicitanteRepository,
    TipoDocumentoRepository,
    HistorialEstadoRepository
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
from app.utils import as_utc_datetime, format_date, format_file_size, format_history_date


class ProposalService:
    """Coordina el registro transaccional de una propuesta."""

    REGISTERED_STATE = "Registrado"
    PROPOSAL_DOCUMENT_TYPE = "propuesta"
    FACULTY_DOCUMENT_TYPE = "facultad"

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
        estado = self.estado_repository.get_by_name(self.REGISTERED_STATE)
        if estado is None:
            raise ValueError(
                "No existe el estado inicial 'Registrado' en la base de datos."
            )

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

        try:
            self.db.flush()


            self.storage_service.ensure_expedition_directory(
                propuesta.uuid_expediente
            )

            solicitante = self.solicitante_repository.create(
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
                    "motivo": "El Postulante registró la propuesta en sistema."
                }
            )

            stored_files.extend(
                self._register_files(
                    files=data.proposal_files,
                    uuid_expediente=propuesta.uuid_expediente,
                    id_propuesta=propuesta.id_propuesta,
                    id_propuesta_solicitante=solicitante.id_propuesta_solicitante,
                    tipo_documento=self.PROPOSAL_DOCUMENT_TYPE,
                )
            )

            stored_files.extend(
                self._register_files(
                    files=data.faculty_files,
                    uuid_expediente=propuesta.uuid_expediente,
                    id_propuesta=propuesta.id_propuesta,
                    id_propuesta_solicitante=solicitante.id_propuesta_solicitante,
                    tipo_documento=self.FACULTY_DOCUMENT_TYPE,
                )
            )

            self.db.commit()
        except Exception:
            self.db.rollback()
            self.storage_service.delete_files(stored_files)
            self.storage_service.delete_expedition_directory(
                propuesta.uuid_expediente
            )
            raise

        return propuesta

    def _register_files(
        self,
        files: list[UploadFile],
        uuid_expediente,
        id_propuesta: int,
        id_propuesta_solicitante: int,
        tipo_documento: str,
    ) -> list[StoredFile]:
        if not files:
            return []

        tipo = self.tipo_documento_repository.get_by_name(tipo_documento)
        if tipo is None:
            raise ValueError(
                f"No existe el tipo de documento '{tipo_documento}' en la base de datos."
            )

        stored_files: list[StoredFile] = []
        
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
                    "id_tipo_documento": tipo.id_tipo_documento,
                    "id_propuesta_solicitante": id_propuesta_solicitante,
                    "ruta_archivo": stored_file.ruta_archivo,
                    "nombre_original": stored_file.nombre_original,
                    "tipo_mime": stored_file.tipo_mime,
                    "tamano_bytes": stored_file.tamano_bytes,
                    "hash_sha256": stored_file.hash_sha256,
                    "estado_carga": "cargado",
                    "fecha_carga": datetime.now(timezone.utc),
                }
            )

        return stored_files

    def list_review(self) -> list[ProposalReviewItem]:
        """Devuelve las propuestas con la información de la vista de revisión."""
        proposals = self.propuesta_repository.get_all_for_review()
        return [self._to_review_item(proposal) for proposal in proposals]

    def _to_review_item(self, propuesta: Propuesta) -> ProposalReviewItem:
        solicitante = propuesta.solicitante
        documents = [
            document
            for document in propuesta.documentos
            if (
                document.es_activo
                and document.es_vigente
                and document.fecha_eliminacion is None
                and document.estado_carga == "cargado"
            )
        ]
        proposal_documents = [
            document
            for document in documents
            if document.tipo_documento.nombre == self.PROPOSAL_DOCUMENT_TYPE
        ]
        faculty_documents = [
            document
            for document in documents
            if document.tipo_documento.nombre == self.FACULTY_DOCUMENT_TYPE
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

        h = history[0] if history else None
        if h is not None:
            print(h.usuario)

        if not history:
            return []

        return [
            ProposalReviewHistory(
                id=f"h-{propuesta.id_propuesta}-{item.id_historial}",
                kind="decision",
                text=self._history_text(item),
                author= item.usuario.nombre if item.usuario is not None else "Postulante",
                date=format_history_date(item.created_at),
            )
            for item in history
        ]

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
    
