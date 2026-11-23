"""Códigos de rol usados para autorizar endpoints.

Los roles viven en la base de datos (tsgp_rol.codigo), no en el token.
"""

try:
    from enum import StrEnum
except ImportError:  # pragma: no cover - compatibilidad con Python < 3.11
    from enum import Enum

    class StrEnum(str, Enum):
        """Implementación compatible de StrEnum para Python anteriores."""


class RolCodigo(StrEnum):
    ADMINISTRADOR = "administrador"
    DIRECCION = "direccion"
    ASISTENTE_DIRECCION = "asistente_direccion"
    EQUIPO_MULTIDISCIPLINAR = "equipo_multidisciplinar"
    # TODO(roles-futuros): agregar juridica, licitaciones y
    # comite_central_extension cuando se definan sus permisos.


# Los cuatro roles que operan el sistema en esta fase.
ROLES_OPERATIVOS: tuple[RolCodigo, ...] = tuple(RolCodigo)
