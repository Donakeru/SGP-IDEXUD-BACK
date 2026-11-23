"""Constantes compartidas para reglas y valores de dominio."""

try:
    from enum import StrEnum
except ImportError:  # pragma: no cover - compatibilidad con Python < 3.11
    from enum import Enum

    class StrEnum(str, Enum):
        """Implementación compatible de StrEnum para Python anteriores."""


from app.core.roles import RolCodigo  # noqa: E402,F401  (se reexporta)


class EstadoPropuestaNombre(StrEnum):
    REGISTRADO = "Registrado"
    ACEPTADO = "Aceptado"
    RECHAZADO = "Rechazado"
    EN_REVISION_DIRECCION = "En Revision por Direccion"
    PREAPROBADO = "Preaprobado"
    APROBADO = "Aprobado"


class TipoDocumentoNombre(StrEnum):
    PROPUESTA = "propuesta"
    FACULTAD = "facultad"


class EstadoCarga(StrEnum):
    PENDIENTE = "pendiente"
    CARGADO = "cargado"
    FALLIDO = "fallido"


class CategoriaComentario(StrEnum):
    """Categorías de un comentario; deben coincidir con ck_com_categoria."""

    VISTO_BUENO = "Visto bueno"
    APROBADO_CON_OBSERVACIONES = "Aprobado con observaciones"
    RECHAZADO = "Rechazado"


# Tipos MIME que el navegador puede mostrar inline sin riesgo de ejecutar
# contenido activo (HTML, SVG, etc.). Cualquier otro tipo se fuerza a descarga.
INLINE_MIME_TYPES = frozenset(
    {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/webp",
        "image/gif",
    }
)


AUTOR_SOLICITANTE = "Postulante"
AUTOR_SISTEMA = "Sistema"
MOTIVO_REGISTRO_INICIAL = "El Postulante registró la propuesta en sistema."
