"""Lógica de negocio relacionada con usuarios."""

from sqlalchemy.orm import Session

from app.models import Rol
from app.repositories import UsuarioRepository


class UsuarioService:
    def __init__(self, db: Session) -> None:
        self.repository = UsuarioRepository(db)

    def get_roles(self, id_usuario: int) -> list[Rol]:
        """Devuelve los roles del usuario. Único punto de lectura de roles.

        TODO(keycloak-roles): puede reemplazarse por los roles de realm del token
        (claim realm_access.roles) si más adelante los roles salen de Keycloak.
        """
        return self.repository.get_roles(id_usuario)
