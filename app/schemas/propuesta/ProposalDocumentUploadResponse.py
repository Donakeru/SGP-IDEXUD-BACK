from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProposalDocumentUploadResponse(BaseModel):
    """Metadatos del documento cargado a una propuesta existente."""

    model_config = ConfigDict(populate_by_name=True)

    id_documento: int = Field(alias="idDocumento")
    uuid_archivo: UUID = Field(alias="uuidArchivo")
    uuid_expediente: UUID = Field(alias="uuidExpediente")
    id_usuario: int = Field(alias="idUsuario")
    nombre_original: str = Field(alias="nombreOriginal")
    tipo_mime: str = Field(alias="tipoMime")
    tamano_bytes: int = Field(alias="tamanoBytes")
    hash_sha256: str | None = Field(alias="hashSha256")
    tipo_documento: str = Field(alias="tipoDocumento")
    numero_version: int = Field(alias="numeroVersion")
    es_vigente: bool = Field(alias="esVigente")
    estado_carga: str = Field(alias="estadoCarga")
    mensaje: str
