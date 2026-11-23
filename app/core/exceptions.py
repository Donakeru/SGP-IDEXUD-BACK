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


class InvalidCommentError(Exception):
    """Indica que el contenido o autor de un comentario no es válido."""


class InvalidCommentCursorError(Exception):
    """Indica que el cursor de comentarios no tiene un formato válido."""


class InvalidUploadError(Exception):
    """Indica que un archivo no cumple los formatos permitidos."""


class UploadTooLargeError(Exception):
    """Indica que un archivo supera el tamaño máximo configurado."""


class InvalidDocumentTypeError(Exception):
    """Indica que el tipo de documento solicitado no está permitido."""


class InvalidDocumentUploaderError(Exception):
    """Indica que el usuario que carga el documento no es válido."""


class InvalidTokenSubjectError(Exception):
    """El claim sub del token no es un UUID válido."""


class TokenEmailMissingError(Exception):
    """El token no incluye el correo electrónico del usuario."""


class EmailNotVerifiedError(Exception):
    """El correo de la cuenta de Keycloak no está verificado."""


class EmailAlreadyLinkedError(Exception):
    """El correo ya pertenece a un usuario vinculado a otra cuenta de Keycloak."""


class UserResolutionError(Exception):
    """No se pudo resolver el usuario local tras varios intentos."""


class TransitionForbiddenError(Exception):
    """El rol del usuario no puede ejecutar una transición de estado válida."""
