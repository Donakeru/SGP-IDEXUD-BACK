"""Repositories de acceso a datos."""

from app.repositories.documento_repository import DocumentoRepository
from app.repositories.lista_repository import ListaRepository
from app.repositories.lista_valor_repository import ListaValorRepository
from app.repositories.propuesta_estado_repository import PropuestaEstadoRepository
from app.repositories.propuesta_repository import PropuestaRepository
from app.repositories.propuesta_solicitante_repository import PropuestaSolicitanteRepository
from app.repositories.tipo_documento_repository import TipoDocumentoRepository
from app.repositories.rol_repository import RolRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.repositories.historial_estado_repository import HistorialEstadoRepository

__all__ = [
    "DocumentoRepository",
    "ListaRepository",
    "ListaValorRepository",
    "PropuestaEstadoRepository",
    "PropuestaRepository",
    "PropuestaSolicitanteRepository",
    "TipoDocumentoRepository",
    "RolRepository",
    "UsuarioRepository",
    "HistorialEstadoRepository"
]
