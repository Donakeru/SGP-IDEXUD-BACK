"""Dependencias compartidas por los routers.

Cadena de autenticación y autorización:

    get_authenticated_user -> get_current_principal -> require_any_role

Solo ``get_authenticated_user`` lee ``settings.auth_mode``. Los routers nunca
consultan el modo: usan ``principal.is_anonymous`` cuando necesitan distinguir si
hay un usuario real detrás de la petición.
"""

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import AUTH_MODE_DEV, settings
from app.core.exceptions import (
    EmailAlreadyLinkedError,
    EmailNotVerifiedError,
    InvalidTokenSubjectError,
    TokenEmailMissingError,
    UserResolutionError,
)
from app.core.principal import ANONYMOUS_PRINCIPAL, Principal, RolInfo
from app.core.roles import RolCodigo
from app.core.security import (
    bearer_scheme,
    extract_bearer_token,
    unauthorized,
    verify_token,
)
from app.db.database import get_db
from app.models import Usuario
from app.services.auth_service import AuthService, get_user_roles

logger = logging.getLogger(__name__)

__all__ = [
    "get_db",
    "get_authenticated_user",
    "get_current_principal",
    "require_any_role",
    "resolve_actor_id",
    "ensure_review_role",
]


def get_authenticated_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ] = None,
    db: Session = Depends(get_db),
) -> Usuario | None:
    """Valida el token y devuelve el usuario local, sin verificar estado ni roles.

    En modo dev devuelve None (no hay usuario real).
    """
    # TODO(dev-mode): el modo dev debe eliminarse antes de desplegar; con él se
    # van esta rama, ANONYMOUS_PRINCIPAL y los usos de principal.is_anonymous.
    if settings.auth_mode == AUTH_MODE_DEV:
        return None

    claims = verify_token(extract_bearer_token(credentials))

    try:
        return AuthService(db).resolve_user(claims)
    except InvalidTokenSubjectError as exc:
        logger.warning("Token con claim sub inválido.")
        raise unauthorized() from exc
    except TokenEmailMissingError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu token no incluye un correo electrónico",
        ) from exc
    except EmailNotVerifiedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El correo de tu cuenta no está verificado en Keycloak",
        ) from exc
    except EmailAlreadyLinkedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo ya está asociado a otra cuenta de Keycloak",
        ) from exc
    except UserResolutionError as exc:
        logger.error("No se pudo resolver el usuario local tras varios intentos.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo resolver el usuario, intenta de nuevo",
        ) from exc


def get_current_principal(
    usuario: Annotated[Usuario | None, Depends(get_authenticated_user)],
    db: Session = Depends(get_db),
) -> Principal:
    """Construye el principal. No rechaza usuarios inactivos ni sin roles."""
    if usuario is None:
        return ANONYMOUS_PRINCIPAL

    roles = get_user_roles(db, usuario.id_usuario)
    return Principal(
        id_usuario=usuario.id_usuario,
        nombre=usuario.nombre,
        correo=usuario.correo,
        es_activo=usuario.es_activo,
        roles=frozenset(rol.codigo for rol in roles),
        roles_info=tuple(RolInfo(codigo=rol.codigo, nombre=rol.nombre) for rol in roles),
    )


def require_any_role(*roles: RolCodigo):
    """Exige que el usuario esté activo, tenga roles y posea alguno de ``roles``.

    Devuelve el principal. En modo dev (principal anónimo) deja pasar siempre.
    """
    allowed = frozenset(role.value for role in roles)

    def role_checker(
        principal: Annotated[Principal, Depends(get_current_principal)],
    ) -> Principal:
        if principal.is_anonymous:
            return principal

        if not principal.es_activo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo",
            )
        if not principal.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu usuario aún no tiene roles asignados",
            )
        if allowed.isdisjoint(principal.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para esta operación",
            )
        return principal

    return role_checker


def resolve_actor_id(principal: Principal, client_id: int | None) -> int:
    """Devuelve el id del usuario que ejecuta la acción.

    Con usuario real se usa siempre el autenticado y se ignora el valor del
    cliente (con un warning si difiere). En modo dev se usa el del cliente.
    """
    if not principal.is_anonymous:
        if client_id is not None and client_id != principal.id_usuario:
            logger.warning(
                "idUsuario enviado por el cliente (%s) difiere del usuario "
                "autenticado (%s); se ignora.",
                client_id,
                principal.id_usuario,
            )
        return principal.id_usuario

    # TODO(dev-mode): eliminar con el modo dev; el autor siempre será el autenticado.
    if client_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="idUsuario es obligatorio",
        )
    return client_id


def ensure_review_role(principal: Principal, rol: str) -> None:
    """Valida el parámetro ``rol`` de la bandeja de revisión (solo con usuario real).

    En modo dev no valida nada, para conservar el comportamiento actual.
    """
    if principal.is_anonymous:
        return

    code = rol.strip().lower()
    valid_codes = [role.value for role in RolCodigo]
    if code not in valid_codes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"El rol debe ser uno de: {', '.join(valid_codes)}",
        )

    if code not in principal.roles and RolCodigo.ADMINISTRADOR.value not in principal.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para consultar la bandeja de ese rol",
        )
