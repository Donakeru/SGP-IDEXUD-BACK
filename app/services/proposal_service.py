"""Servicio para registrar propuestas, solicitantes y documentos."""

import base64
import binascii
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.constants import (
    AUTOR_SISTEMA,
    INLINE_MIME_TYPES,
    CategoriaComentario,
    MOTIVO_REGISTRO_INICIAL,
    EstadoCarga,
    EstadoPropuestaNombre,
    RolCodigo,
    TipoDocumentoNombre,
)
from app.core.exceptions import (
    ConfigurationError,
    DocumentNotFoundError,
    InvalidCommentCursorError,
    InvalidCommentError,
    InvalidDocumentTypeError,
    InvalidDocumentUploaderError,
    InvalidProposalTransitionError,
    InvalidTransitionActorError,
    ProposalNotFoundError,
    ProposalStateNotFoundError,
    TransitionForbiddenError,
    UnsupportedReviewRoleError,
)
from app.core.transitions import roles_for_transition
from app.models.comentario import Comentario
from app.models.documento import Documento
from app.models.propuesta import Propuesta
from app.models.tipo_documento import TipoDocumento
from app.repositories import (
    ComentarioRepository,
    DocumentoRepository,
    HistorialEstadoRepository,
    PropuestaEstadoRepository,
    PropuestaRepository,
    PropuestaSolicitanteRepository,
    TipoDocumentoRepository,
    UsuarioRepository,
)
from app.schemas.propuesta import (
    CreateProposalDto,
    ProposalComment,
    ProposalComments,
    ProposalDetailResponse,
    ProposalDocumentUploadResponse,
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


@dataclass(frozen=True)
class DocumentFile:
    """Archivo de un documento listo para enviarse al cliente."""

    path: Path
    filename: str
    media_type: str
    inline_allowed: bool


@dataclass(frozen=True)
class ProposalStateChangeResult:
    """Resultado de una transición de estado confirmada."""

    propuesta: Propuesta
    estado_anterior: str
    estado_nuevo: str
    motivo: str | None


class ProposalService:
    """Coordina el registro transaccional de una propuesta."""

    REVIEW_STATES_BY_ROLE: dict[str, tuple[str, ...]] = {
        RolCodigo.ASISTENTE_DIRECCION.value: (
            EstadoPropuestaNombre.REGISTRADO.value,
            EstadoPropuestaNombre.RECHAZADO.value,
        ),
        RolCodigo.DIRECCION.value: (
            EstadoPropuestaNombre.EN_REVISION_DIRECCION.value,
        ),
    }

    def __init__(self, db: Session) -> None:
        self.db = db
        self.propuesta_repository = PropuestaRepository(db)
        self.comentario_repository = ComentarioRepository(db)
        self.historial_estado_repository = HistorialEstadoRepository(db)
        self.estado_repository = PropuestaEstadoRepository(db)
        self.solicitante_repository = PropuestaSolicitanteRepository(db)
        self.documento_repository = DocumentoRepository(db)
        self.tipo_documento_repository = TipoDocumentoRepository(db)
        self.usuario_repository = UsuarioRepository(db)
        self.storage_service = StorageService()

    def list_proposals(self, offset: int, limit: int) -> ProposalListResponse:
        """Devuelve una página de propuestas para la tabla del frontend."""
        proposals, total = self.propuesta_repository.get_page(
            offset=offset,
            limit=limit,
            state_name=EstadoPropuestaNombre.ACEPTADO.value,
        )

        items = [
            ProposalListItem(
                id_propuesta=propuesta.id_propuesta,
                uuid_expediente=propuesta.uuid_expediente,
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

    def create_proposal(
        self,
        data: CreateProposalDto,
        author_user_id: int | None = None,
    ) -> Propuesta:
        """Registra propuesta, solicitante y archivos en una transacción.

        Los datos ``proposal_type`` todavía no se guardan porque la tabla de
        propuestas aún no tiene una columna para ese valor.

        Si ``author_user_id`` es None (modo dev), el autor del historial y de los
        documentos es el solicitante. Si trae un id (modo keycloak), el autor es
        ese usuario autenticado y ``id_propuesta_solicitante`` queda en nulo, porque
        los CHECK ``chk_he_autor`` y ``chk_doc_autor`` exigen exactamente un autor.
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

            id_solicitante_autor = (
                solicitante.id_propuesta_solicitante if author_user_id is None else None
            )

            self.historial_estado_repository.add(
                {
                    "id_propuesta": propuesta.id_propuesta,
                    "id_estado_anterior": None,
                    "id_estado_nuevo": estado.id_propuesta_estado,
                    "id_usuario": author_user_id,
                    "id_propuesta_solicitante": id_solicitante_autor,
                    "motivo": MOTIVO_REGISTRO_INICIAL,
                }
            )

            self._register_files(
                files=data.proposal_files,
                stored_files=stored_files,
                uuid_expediente=uuid_expediente,
                id_propuesta=propuesta.id_propuesta,
                id_propuesta_solicitante=id_solicitante_autor,
                id_usuario=author_user_id,
                tipo_documento=proposal_document_type,
            )
            self._register_files(
                files=data.faculty_files,
                stored_files=stored_files,
                uuid_expediente=uuid_expediente,
                id_propuesta=propuesta.id_propuesta,
                id_propuesta_solicitante=id_solicitante_autor,
                id_usuario=author_user_id,
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
        id_propuesta_solicitante: int | None,
        tipo_documento: TipoDocumento,
        id_usuario: int | None = None,
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
                    "id_usuario": id_usuario,
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

    def upload_document(
        self,
        uuid_expediente: UUID,
        upload: UploadFile,
        id_usuario: int,
        tipo_documento: str,
    ) -> ProposalDocumentUploadResponse:
        """Carga un documento de un usuario activo a una propuesta existente."""
        propuesta = self.propuesta_repository.get_by_uuid_for_update(uuid_expediente)
        if propuesta is None:
            raise ProposalNotFoundError(
                f"No existe una propuesta para el expediente '{uuid_expediente}'."
            )

        usuario = self.usuario_repository.get_by_id(id_usuario)
        if usuario is None or not usuario.es_activo:
            raise InvalidDocumentUploaderError(
                "El usuario que carga el documento no existe o está inactivo."
            )

        try:
            document_type_name = TipoDocumentoNombre(tipo_documento.strip().lower())
        except ValueError as exc:
            raise InvalidDocumentTypeError(
                "El tipo de documento debe ser 'propuesta' o 'facultad'."
            ) from exc
        document_type = self._get_document_type(document_type_name)

        stored_files: list[StoredFile] = []
        try:
            stored_file = self.storage_service.save_upload(
                upload=upload,
                uuid_expediente=uuid_expediente,
            )
            stored_files.append(stored_file)

            documento = self.documento_repository.add(
                {
                    "uuid_archivo": stored_file.uuid_archivo,
                    "id_propuesta": propuesta.id_propuesta,
                    "id_tipo_documento": document_type.id_tipo_documento,
                    "id_usuario": id_usuario,
                    "id_propuesta_solicitante": None,
                    "ruta_archivo": stored_file.ruta_archivo,
                    "nombre_original": stored_file.nombre_original,
                    "tipo_mime": stored_file.tipo_mime,
                    "tamano_bytes": stored_file.tamano_bytes,
                    "hash_sha256": stored_file.hash_sha256,
                    "numero_version": 1,
                    "es_vigente": True,
                    "estado_carga": EstadoCarga.CARGADO.value,
                    "fecha_carga": datetime.now(timezone.utc),
                    "es_activo": True,
                }
            )
            self.db.flush()
            self.db.commit()
        except Exception:
            self.db.rollback()
            self.storage_service.delete_files(stored_files)
            raise

        return ProposalDocumentUploadResponse(
            idDocumento=documento.id_documento,
            uuidArchivo=stored_file.uuid_archivo,
            uuidExpediente=uuid_expediente,
            idUsuario=id_usuario,
            nombreOriginal=stored_file.nombre_original,
            tipoMime=stored_file.tipo_mime,
            tamanoBytes=stored_file.tamano_bytes,
            hashSha256=stored_file.hash_sha256,
            tipoDocumento=document_type.nombre,
            numeroVersion=documento.numero_version,
            esVigente=documento.es_vigente,
            estadoCarga=documento.estado_carga,
            mensaje="Documento cargado correctamente.",
        )

    def get_document_file(self, uuid_archivo: UUID) -> DocumentFile:
        """Busca un documento por uuid_archivo y resuelve su archivo en disco.

        Lanza DocumentNotFoundError si no existe, no está activo, no está
        cargado, fue eliminado o el archivo no está disponible en disco.
        """
        documento = self.documento_repository.get_by_uuid(uuid_archivo)
        if (
            documento is None
            or not documento.es_activo
            or documento.es_vigente is False
            or documento.fecha_eliminacion is not None
            or documento.estado_carga != EstadoCarga.CARGADO.value
        ):
            raise DocumentNotFoundError(f"Documento {uuid_archivo} no disponible.")

        path = self.storage_service.resolve_stored_path(documento.ruta_archivo)
        base_mime = documento.tipo_mime.split(";")[0].strip().lower()
        # Solo el nombre, sin directorios, para el encabezado Content-Disposition.
        filename = PureWindowsPath(documento.nombre_original).name or str(uuid_archivo)

        return DocumentFile(
            path=path,
            filename=filename,
            media_type=documento.tipo_mime,
            inline_allowed=base_mime in INLINE_MIME_TYPES,
        )

    def change_proposal_status(
        self,
        uuid_expediente: UUID,
        estado_destino: str,
        id_usuario: int,
        motivo: str | None = None,
        actor_roles: frozenset[str] | None = None,
    ) -> ProposalStateChangeResult:
        """Cambia el estado permitido y registra el evento en el historial.

        Con ``actor_roles`` (modo keycloak) la transición debe estar en la matriz
        de ``app.core.transitions`` y el rol debe poder ejecutarla. Con ``None``
        (modo dev) no se valida la matriz, igual que antes.
        """
        target_name = estado_destino.strip()
        propuesta = self.propuesta_repository.get_by_uuid_for_update(
            uuid_expediente
        )
        if propuesta is None:
            raise ProposalNotFoundError(
                f"No existe una propuesta para el expediente '{uuid_expediente}'."
            )

        current_name = propuesta.estado.nombre
        current_state_id = propuesta.id_propuesta_estado
        estado_nuevo = self.estado_repository.get_by_name(target_name)
        if estado_nuevo is None:
            raise ProposalStateNotFoundError(
                f"No existe el estado destino '{target_name}' en la base de datos."
            )

        if current_state_id == estado_nuevo.id_propuesta_estado:
            raise InvalidProposalTransitionError(
                f"La propuesta ya se encuentra en el estado '{current_name}'."
            )

        if actor_roles is not None:
            allowed_roles = roles_for_transition(current_name, target_name)
            if allowed_roles is None:
                raise InvalidProposalTransitionError(
                    "Transición de estado no permitida"
                )
            if allowed_roles.isdisjoint(actor_roles):
                raise TransitionForbiddenError(
                    "No tienes permisos para esta transición"
                )

        usuario = self.usuario_repository.get_by_id(id_usuario)
        if usuario is None or not usuario.es_activo:
            raise InvalidTransitionActorError(
                "El usuario que ejecuta la transición no existe o está inactivo."
            )

        clean_reason = motivo.strip() if motivo and motivo.strip() else None
        try:
            propuesta.id_propuesta_estado = estado_nuevo.id_propuesta_estado
            propuesta.estado = estado_nuevo
            propuesta.updated_at = datetime.now(timezone.utc)
            self.db.flush()

            self.historial_estado_repository.add(
                {
                    "id_propuesta": propuesta.id_propuesta,
                    "id_estado_anterior": current_state_id,
                    "id_estado_nuevo": estado_nuevo.id_propuesta_estado,
                    "id_usuario": id_usuario,
                    "id_propuesta_solicitante": None,
                    "motivo": clean_reason,
                }
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return ProposalStateChangeResult(
            propuesta=propuesta,
            estado_anterior=current_name,
            estado_nuevo=target_name,
            motivo=clean_reason,
        )

    def list_review(self, rol: str) -> list[ProposalReviewItem]:
        """Devuelve la bandeja de revisión correspondiente al rol."""
        role_code = rol.strip().lower()
        state_names = self.REVIEW_STATES_BY_ROLE.get(role_code)
        if state_names is None:
            raise UnsupportedReviewRoleError(
                f"No existe una bandeja configurada para el rol '{rol}'."
            )

        proposals = self.propuesta_repository.get_all_for_review(
            state_names=state_names,
        )
        return [self._to_review_item(proposal) for proposal in proposals]

    def get_proposal_detail(self, uuid_expediente: UUID) -> ProposalDetailResponse:
        """Devuelve la estructura de revisión con los comentarios más recientes."""
        propuesta = self.propuesta_repository.get_by_uuid_for_detail(uuid_expediente)
        if propuesta is None:
            raise ProposalNotFoundError(
                f"No existe una propuesta para el expediente '{uuid_expediente}'."
            )

        comments = self.list_comments(uuid_expediente, cursor=None)
        review_item = self._to_review_item(propuesta)
        return ProposalDetailResponse(
            **review_item.model_dump(),
            comments=comments,
        )

    def list_comments(
        self,
        uuid_expediente: UUID,
        cursor: str | None = None,
    ) -> ProposalComments:
        """Devuelve comentarios recientes y un cursor para la siguiente página."""
        propuesta = self.propuesta_repository.get_by_uuid(uuid_expediente)
        if propuesta is None:
            raise ProposalNotFoundError(
                f"No existe una propuesta para el expediente '{uuid_expediente}'."
            )

        decoded_cursor = self._decode_comment_cursor(cursor) if cursor else None
        comments, total = self.comentario_repository.get_page(
            id_propuesta=propuesta.id_propuesta,
            limit=3,
            cursor=decoded_cursor,
        )
        has_next = len(comments) > 3
        page = comments[:3]
        next_cursor = (
            self._encode_comment_cursor(page[-1])
            if has_next and page
            else None
        )
        return ProposalComments(
            items=[self._to_comment_item(comment) for comment in page],
            total=total,
            next_cursor=next_cursor,
        )

    def create_comment(
        self,
        uuid_expediente: UUID,
        content: str,
        id_usuario: int,
        category: str = CategoriaComentario.VISTO_BUENO.value,
        document_uuid: UUID | None = None,
    ) -> ProposalComment:
        """Registra un comentario asociado a una propuesta existente.

        ``document_uuid`` (opcional) es el documento sobre el que se hace la
        observación; debe pertenecer a la misma propuesta.
        """
        propuesta = self.propuesta_repository.get_by_uuid_for_update(uuid_expediente)
        if propuesta is None:
            raise ProposalNotFoundError(
                f"No existe una propuesta para el expediente '{uuid_expediente}'."
            )

        usuario = self.usuario_repository.get_by_id(id_usuario)
        if usuario is None or not usuario.es_activo:
            raise InvalidCommentError(
                "El usuario que registra el comentario no existe o está inactivo."
            )

        clean_content = content.strip()
        if not clean_content:
            raise InvalidCommentError("El comentario no puede estar vacío.")

        documento: Documento | None = None
        if document_uuid is not None:
            documento = self.documento_repository.get_by_uuid(document_uuid)
            if (
                documento is None
                or documento.id_propuesta != propuesta.id_propuesta
                or not documento.es_activo
                or documento.fecha_eliminacion is not None
            ):
                raise InvalidCommentError(
                    "El documento relacionado no existe o no pertenece a la propuesta."
                )

        try:
            comentario = self.comentario_repository.add(
                {
                    "id_propuesta": propuesta.id_propuesta,
                    "id_usuario": id_usuario,
                    "contenido": clean_content,
                    "categoria": category,
                    "id_documento": documento.id_documento if documento else None,
                }
            )
            comentario.usuario = usuario
            comentario.documento = documento
            self.db.flush()
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return self._to_comment_item(comentario)

    @staticmethod
    def _encode_comment_cursor(comment: Comentario) -> str:
        payload = json.dumps(
            {
                "created_at": comment.created_at.isoformat(),
                "id": comment.id_comentario,
            },
            separators=(",", ":"),
        ).encode()
        return base64.urlsafe_b64encode(payload).decode().rstrip("=")

    @staticmethod
    def _decode_comment_cursor(cursor: str) -> tuple[datetime, int]:
        try:
            padding = "=" * (-len(cursor) % 4)
            payload = json.loads(
                base64.urlsafe_b64decode((cursor + padding).encode()).decode()
            )
            created_at = datetime.fromisoformat(payload["created_at"])
            comment_id = int(payload["id"])
            if created_at.tzinfo is None or comment_id <= 0:
                raise ValueError
            return created_at, comment_id
        except (
            binascii.Error,
            UnicodeDecodeError,
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            raise InvalidCommentCursorError(
                "El cursor de comentarios no es válido."
            ) from exc

    @staticmethod
    def _to_comment_item(comment: Comentario) -> ProposalComment:
        return ProposalComment(
            id=comment.id_comentario,
            content=comment.contenido,
            author=comment.usuario.nombre if comment.usuario else AUTOR_SISTEMA,
            createdAt=comment.created_at,
            category=comment.categoria,
            documentUuid=comment.documento.uuid_archivo if comment.documento else None,
            documentName=(
                comment.documento.nombre_original if comment.documento else None
            ),
        )

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
            uuid_expediente=propuesta.uuid_expediente,
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
                    id_documento=document.id_documento,
                    uuid_archivo=document.uuid_archivo,
                    nombre_original=document.nombre_original,
                    tipo_mime=document.tipo_mime,
                    tamano_bytes=document.tamano_bytes,
                    numero_version=document.numero_version,
                    es_vigente=document.es_vigente,
                    tipo_documento=document.tipo_documento.nombre,
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
                text=self._history_text(item),
                subject=self._history_subject(item),
                author=self._history_author(item),
                date=format_history_date(item.created_at),
            )
            for item in history
        ]

    @staticmethod
    def _history_subject(item) -> str | None:
        return item.motivo

    @staticmethod
    def _history_author(item) -> str:
        if item.usuario is not None:
            return item.usuario.nombre
        if item.solicitante is not None:
            return item.solicitante.nombre_contacto
        return AUTOR_SISTEMA

    @staticmethod
    def _history_text(item) -> str:
        if item.estado_anterior is None:
            return f'Propuesta registrada en estado "{item.estado_nuevo.nombre}".'
        return (
            f'Propuesta cambió de "{item.estado_anterior.nombre}" '
            f'a "{item.estado_nuevo.nombre}".'
        )
