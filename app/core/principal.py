"""Representación del usuario que realiza la petición."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RolInfo:
    codigo: str
    nombre: str


@dataclass(frozen=True)
class Principal:
    """Estado real del usuario de la petición.

    No rechaza a nadie por sí mismo: un usuario inactivo o sin roles se
    representa tal cual. Los 403 los aplica require_any_role.
    """

    id_usuario: int | None
    nombre: str
    correo: str | None
    es_activo: bool
    roles: frozenset[str]
    roles_info: tuple[RolInfo, ...] = ()

    @property
    def is_anonymous(self) -> bool:
        """True en modo dev: no hay usuario real detrás de la petición."""
        return self.id_usuario is None


# TODO(dev-mode): eliminar junto con el modo dev antes de desplegar.
ANONYMOUS_PRINCIPAL = Principal(
    id_usuario=None,
    nombre="Anónimo (dev)",
    correo=None,
    es_activo=True,
    roles=frozenset(),
)
