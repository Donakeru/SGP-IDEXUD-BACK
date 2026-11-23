from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import Comentario


class ComentarioRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, data: dict[str, Any]) -> Comentario:
        comentario = Comentario(**data)
        self.db.add(comentario)
        return comentario

    def get_page(
        self,
        id_propuesta: int,
        limit: int,
        cursor: tuple[datetime, int] | None = None,
    ) -> tuple[list[Comentario], int]:
        """Obtiene comentarios recientes con paginación por cursor."""
        base_filter = Comentario.id_propuesta == id_propuesta
        total = self.db.scalar(
            select(func.count(Comentario.id_comentario)).where(base_filter)
        ) or 0

        statement = (
            select(Comentario)
            .options(
                joinedload(Comentario.usuario),
                joinedload(Comentario.documento),
            )
            .where(base_filter)
        )
        if cursor is not None:
            cursor_created_at, cursor_id = cursor
            statement = statement.where(
                or_(
                    Comentario.created_at < cursor_created_at,
                    and_(
                        Comentario.created_at == cursor_created_at,
                        Comentario.id_comentario < cursor_id,
                    ),
                )
            )

        comments = list(
            self.db.scalars(
                statement.order_by(
                    Comentario.created_at.desc(),
                    Comentario.id_comentario.desc(),
                ).limit(limit + 1)
            ).unique().all()
        )
        return comments, total
