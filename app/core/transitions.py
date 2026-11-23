"""Matriz de transiciones de estado de una propuesta y los roles que las ejecutan.

Es la única fuente de verdad para PATCH /proposal/{uuid}/status. Los nombres de
estado coinciden con tsgp_propuesta_estado.nombre.

- Una transición que no está en la matriz no está permitida (409).
- Una transición listada solo la ejecutan los roles indicados y el administrador,
  que puede todas (403 para cualquier otro rol).
- En modo dev la matriz no se aplica.

TODO: cuando se decida el modelo de permisos por transición, esta matriz puede
leerse de tsgp_transicion_estado (id_permiso) en lugar de estar en código.
"""

from app.core.constants import EstadoPropuestaNombre as Estado
from app.core.roles import RolCodigo as Rol

Transition = tuple[str, str]

# Roles, además del administrador, que pueden ejecutar cada transición.
# frozenset() significa "solo administrador".
TRANSITION_ROLES: dict[Transition, frozenset[str]] = {
    (Estado.REGISTRADO.value, Estado.EN_REVISION_DIRECCION.value): frozenset(
        {Rol.ASISTENTE_DIRECCION.value}
    ),
    (Estado.REGISTRADO.value, Estado.RECHAZADO.value): frozenset(
        {Rol.ASISTENTE_DIRECCION.value}
    ),
    (Estado.EN_REVISION_DIRECCION.value, Estado.ACEPTADO.value): frozenset(
        {Rol.DIRECCION.value}
    ),
    (Estado.EN_REVISION_DIRECCION.value, Estado.RECHAZADO.value): frozenset(
        {Rol.DIRECCION.value}
    ),
    # TODO: habilitar Jurídica y Licitaciones para esta transición.
    (Estado.ACEPTADO.value, Estado.PREAPROBADO.value): frozenset(),
    # TODO: habilitar el Comité Central de Extensión para estas dos transiciones.
    (Estado.PREAPROBADO.value, Estado.APROBADO.value): frozenset(),
    (Estado.PREAPROBADO.value, Estado.RECHAZADO.value): frozenset(),
}


def roles_for_transition(origen: str, destino: str) -> frozenset[str] | None:
    """Devuelve los roles que pueden ejecutar la transición, o None si no existe."""
    allowed = TRANSITION_ROLES.get((origen, destino))
    if allowed is None:
        return None
    return allowed | {Rol.ADMINISTRADOR.value}
