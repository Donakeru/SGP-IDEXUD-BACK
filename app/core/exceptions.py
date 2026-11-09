"""Excepciones propias de la lógica de aplicación."""


class ConfigurationError(Exception):
    """Indica que falta una configuración requerida en la base de datos."""
