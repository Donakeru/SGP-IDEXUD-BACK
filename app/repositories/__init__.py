"""Repositories de acceso a datos."""

from app.repositories.documento_repository import DocumentoRepository
from app.repositories.historial_estado_repository import HistorialEstadoRepository
from app.repositories.lista_repository import ListaRepository
from app.repositories.lista_valor_repository import ListaValorRepository
from app.repositories.propuesta_estado_repository import PropuestaEstadoRepository
from app.repositories.propuesta_repository import PropuestaRepository
from app.repositories.propuesta_solicitante_repository import (
    PropuestaSolicitanteRepository,
)
from app.repositories.rol_repository import RolRepository
from app.repositories.tipo_documento_repository import TipoDocumentoRepository
from app.repositories.usuario_repository import UsuarioRepository

__all__ = [
    "DocumentoRepository",
    "HistorialEstadoRepository",
    "ListaRepository",
    "ListaValorRepository",
    "PropuestaEstadoRepository",
    "PropuestaRepository",
    "PropuestaSolicitanteRepository",
    "RolRepository",
    "TipoDocumentoRepository",
    "UsuarioRepository",
]
