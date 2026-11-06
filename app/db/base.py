"""Base declarativa compartida por todos los modelos ORM."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Registro declarativo de las tablas de la aplicación."""
