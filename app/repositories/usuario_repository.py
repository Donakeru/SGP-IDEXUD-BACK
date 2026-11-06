from sqlalchemy.orm import Session

from app.models.usuario import Usuario


class UsuarioRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, id_usuario: int) -> Usuario | None:
        return self.db.get(Usuario, id_usuario)
