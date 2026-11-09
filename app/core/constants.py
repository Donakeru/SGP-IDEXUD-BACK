"""Constantes compartidas para reglas y valores de dominio."""

try:
    from enum import StrEnum
except ImportError:  # pragma: no cover - compatibilidad con Python < 3.11
    from enum import Enum

    class StrEnum(str, Enum):
        """Implementación compatible de StrEnum para Python anteriores."""


class EstadoPropuestaNombre(StrEnum):
    REGISTRADO = "Registrado"


class TipoDocumentoNombre(StrEnum):
    PROPUESTA = "propuesta"
    FACULTAD = "facultad"


class EstadoCarga(StrEnum):
    PENDIENTE = "pendiente"
    CARGADO = "cargado"
    FALLIDO = "fallido"


class HistoryKind(StrEnum):
    DECISION = "decision"


AUTOR_SOLICITANTE = "Postulante"
AUTOR_SISTEMA = "Sistema"
MOTIVO_REGISTRO_INICIAL = "El Postulante registró la propuesta en sistema."
