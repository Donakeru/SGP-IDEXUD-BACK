"""Base declarativa compartida por todos los modelos ORM."""

from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Registro declarativo de las tablas de la aplicación."""
    def __repr__(self) -> str:
        mapper = inspect(self).mapper
        campos = ", ".join(
            f"{col.key}={getattr(self, col.key, None)!r}"
            for col in mapper.column_attrs
        )
        return f"{self.__class__.__name__}({campos})"
