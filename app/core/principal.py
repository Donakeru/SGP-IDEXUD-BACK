"""Representación del usuario que realiza la petición."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Principal:
    """Estado real del usuario de la petición.

    No rechaza a nadie por sí mismo: un usuario inactivo o sin roles se
    representa tal cual. Los 403 los aplica require_any_role.
    """

    id_usuario: int
    nombre: str
    correo: str
    es_activo: bool
    roles: frozenset[str]
