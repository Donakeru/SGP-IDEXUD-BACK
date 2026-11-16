"""Excepciones propias de la lógica de aplicación."""


class ConfigurationError(Exception):
    """Indica que falta una configuración requerida en la base de datos."""


class DocumentNotFoundError(Exception):
    """El documento no existe, no está disponible o su archivo no es accesible."""
