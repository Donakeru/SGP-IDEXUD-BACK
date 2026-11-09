"""Lógica de negocio relacionada con usuarios."""

from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.repositories import UsuarioRepository


class UsuarioService:
    def __init__(self, db: Session) -> None:
        self.repository = UsuarioRepository(db)

    def get_by_id(self, id_usuario: int) -> Usuario | None:
        return self.repository.get_by_id(id_usuario)
