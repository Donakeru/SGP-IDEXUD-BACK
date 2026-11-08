"""Servicio para registrar propuestas, solicitantes y documentos."""

from datetime import datetime, timezone

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.propuesta import Propuesta
from app.repositories.documento_repository import DocumentoRepository
from app.repositories.propuesta_estado_repository import PropuestaEstadoRepository
from app.repositories.propuesta_repository import PropuestaRepository
from app.repositories.propuesta_solicitante_repository import (
    PropuestaSolicitanteRepository,
)
from app.repositories.tipo_documento_repository import TipoDocumentoRepository
from app.schemas.propuesta import (
    CreateProposalDto,
    ProposalListItem,
    ProposalListResponse,
)
from app.services.storage_service import StorageService, StoredFile
from app.utils.date_utils import as_utc_datetime


class ProposalService:
    """Coordina el registro transaccional de una propuesta."""

    REGISTERED_STATE = "Registrado"
    PROPOSAL_DOCUMENT_TYPE = "propuesta"
    FACULTY_DOCUMENT_TYPE = "facultad"

    # TODO: reemplazar por el usuario autenticado cuando exista esa dependencia.
    DEFAULT_STORAGE_USER_ID = 1

    def __init__(self, db: Session) -> None:
        self.db = db
        self.propuesta_repository = PropuestaRepository(db)
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

            self.solicitante_repository.add(
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

            stored_files.extend(
                self._register_files(
                    files=data.proposal_files,
                    uuid_expediente=propuesta.uuid_expediente,
                    id_propuesta=propuesta.id_propuesta,
                    tipo_documento=self.PROPOSAL_DOCUMENT_TYPE,
                )
            )
            stored_files.extend(
                self._register_files(
                    files=data.faculty_files,
                    uuid_expediente=propuesta.uuid_expediente,
                    id_propuesta=propuesta.id_propuesta,
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
                    "id_usuario": self.DEFAULT_STORAGE_USER_ID,
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
