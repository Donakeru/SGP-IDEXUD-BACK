"""Engine y sesiones síncronas de PostgreSQL."""

import logging
from collections.abc import Generator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

engine: Engine = create_engine(
    settings.get_database_url(),
    echo=settings.environment.lower() == "development",
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    expire_on_commit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """Proporciona una sesión síncrona por solicitud."""
    with SessionLocal() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise


def check_database_connection() -> None:
    """Verifica que PostgreSQL acepte conexiones."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.error(
            "No se pudo conectar a PostgreSQL en %s:%s (base de datos: %s).",
            settings.db_host,
            settings.db_port,
            settings.db_name,
        )
        raise RuntimeError("No hay conexión con la base de datos.") from exc
    logger.info("Conexión a PostgreSQL verificada correctamente.")


def close_database_connection() -> None:
    """Libera las conexiones abiertas del pool."""
    engine.dispose()
