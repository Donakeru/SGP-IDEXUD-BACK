from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models import Rol, Usuario, UsuarioRol


class UsuarioRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, id_usuario: int) -> Usuario | None:
        return self.db.get(Usuario, id_usuario)

    def get_by_keycloak_sub(self, keycloak_sub: UUID) -> Usuario | None:
        statement = select(Usuario).where(Usuario.keycloak_sub == keycloak_sub)
        return self.db.scalar(statement)

    def get_by_correo(self, correo: str) -> Usuario | None:
        """Busca por correo sin distinguir mayúsculas."""
        statement = select(Usuario).where(func.lower(Usuario.correo) == correo.lower())
        return self.db.scalar(statement)

    def add(self, data: dict[str, Any]) -> Usuario:
        """Agrega un usuario a la sesión sin confirmar la transacción."""
        usuario = Usuario(**data)
        self.db.add(usuario)
        return usuario

    def link_keycloak_sub(self, id_usuario: int, keycloak_sub: UUID) -> bool:
        """Vincula el sub solo si el usuario aún no tiene uno.

        Devuelve False si otra petición lo vinculó antes.
        """
        statement = (
            update(Usuario)
            .where(
                Usuario.id_usuario == id_usuario,
                Usuario.keycloak_sub.is_(None),
            )
            .values(keycloak_sub=keycloak_sub)
        )
        return self.db.execute(statement).rowcount == 1

    def get_roles(self, id_usuario: int) -> list[Rol]:
        """Devuelve los roles asignados al usuario, ordenados por código."""
        statement = (
            select(Rol)
            .join(UsuarioRol, UsuarioRol.id_rol == Rol.id_rol)
            .where(UsuarioRol.id_usuario == id_usuario)
            .order_by(Rol.codigo)
        )
        return list(self.db.scalars(statement).all())
