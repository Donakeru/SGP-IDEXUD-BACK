"""Dependencias compartidas por los routers.

Cadena de autenticación y autorización (Keycloak es el único modo):

    get_authenticated_user -> get_current_principal -> require_any_role

Todo endpoint protegido depende de ``get_authenticated_user`` (directamente o a
través de ``require_any_role``), que siempre valida el token Bearer.
"""

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.exceptions import (
    EmailAlreadyLinkedError,
    EmailNotVerifiedError,
    InvalidTokenSubjectError,
    TokenEmailMissingError,
    UserResolutionError,
)
from app.core.principal import Principal
from app.core.roles import RolCodigo
from app.core.security import (
    bearer_scheme,
    extract_bearer_token,
    unauthorized,
    verify_token,
)
from app.db.database import get_db
from app.models import Usuario
from app.services.auth_service import AuthService
from app.services.usuario_service import UsuarioService

logger = logging.getLogger(__name__)

__all__ = [
    "get_db",
    "AuthenticatedUser",
    "get_authenticated_user",
    "get_current_principal",
    "require_any_role",
    "ensure_review_role",
]


def get_authenticated_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ] = None,
    db: Session = Depends(get_db),
) -> Usuario:
    """Valida el token y devuelve el usuario local, sin verificar estado ni roles."""
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


# Usuario local del token. Los routers lo usan como tipo para no importar el modelo:
# `usuario: AuthenticatedUser`.
AuthenticatedUser = Annotated[Usuario, Depends(get_authenticated_user)]


def get_current_principal(
    usuario: AuthenticatedUser,
    db: Session = Depends(get_db),
) -> Principal:
    """Construye el principal. No rechaza usuarios inactivos ni sin roles."""
    roles = UsuarioService(db).get_roles(usuario.id_usuario)
    return Principal(
        id_usuario=usuario.id_usuario,
        nombre=usuario.nombre,
        correo=usuario.correo,
        es_activo=usuario.es_activo,
        roles=frozenset(rol.codigo for rol in roles),
    )


def require_any_role(*roles: RolCodigo):
    """Exige que el usuario esté activo, tenga roles y posea alguno de ``roles``.

    Devuelve el principal.
    """
    allowed = frozenset(role.value for role in roles)

    def role_checker(
        principal: Annotated[Principal, Depends(get_current_principal)],
    ) -> Principal:
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


def ensure_review_role(principal: Principal, rol: str) -> None:
    """Valida el parámetro ``rol`` de la bandeja de revisión.

    Debe ser uno de los cuatro códigos (422) y el principal debe tener ese rol o ser
    administrador (403).
    """
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
