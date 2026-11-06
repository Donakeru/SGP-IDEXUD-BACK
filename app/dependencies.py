"""Dependencias compartidas por los routers."""

from app.db.database import get_db

__all__ = ["get_db"]
