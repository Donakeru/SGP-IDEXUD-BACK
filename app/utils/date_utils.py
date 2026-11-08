"""Utilidades para normalizar fechas y horas."""

from datetime import date, datetime, time, timezone


def as_utc_datetime(value: date | datetime) -> datetime:
    """Convierte una fecha o datetime en un datetime consciente en UTC."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    return datetime.combine(value, time.min, tzinfo=timezone.utc)
