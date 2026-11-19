"""Excepciones propias de la lógica de aplicación."""


class ProposalStateNotFoundError(Exception):
    """Indica que el estado destino no existe en la base de datos."""


class ProposalNotFoundError(Exception):
    """Indica que no existe una propuesta con el identificador solicitado."""


class InvalidProposalTransitionError(Exception):
    """Indica que el estado actual no permite la transición solicitada."""


class InvalidTransitionActorError(Exception):
    """Indica que el usuario que ejecuta la transición no es válido."""


class ConfigurationError(Exception):
    """Indica que falta una configuración requerida en la base de datos."""


class DocumentNotFoundError(Exception):
    """El documento no existe, no está disponible o su archivo no es accesible."""


class UnsupportedReviewRoleError(Exception):
    """Indica que el rol no tiene una bandeja de revisión configurada."""
