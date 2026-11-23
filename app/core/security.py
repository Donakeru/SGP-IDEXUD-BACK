"""Validación de tokens JWT emitidos por Keycloak.

Portado de docs/plantilla-keycloack/security.py. La autorización por rol no
vive aquí: los roles se leen de la base de datos (ver app/services/auth_service.py).
"""

import logging
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientConnectionError, PyJWTError

from app.core.config import settings

logger = logging.getLogger(__name__)

# auto_error=False: la respuesta 401 la construimos nosotros (sin detalles internos).
bearer_scheme = HTTPBearer(auto_error=False)

UNAUTHORIZED_DETAIL = "Token ausente, inválido o expirado"
AUTH_UNAVAILABLE_DETAIL = "Servicio de autenticación no disponible"
TOKEN_LEEWAY_SECONDS = 30
JWKS_TIMEOUT_SECONDS = 10

_jwks_client: PyJWKClient | None = None


def init_jwks_client() -> None:
    """Crea el cliente JWKS. Se llama una vez, al arrancar la aplicación.

    El constructor no hace red: la primera consulta ocurre con el primer token.
    """
    global _jwks_client
    _jwks_client = PyJWKClient(
        settings.keycloak_jwks_url,
        cache_jwk_set=True,
        timeout=JWKS_TIMEOUT_SECONDS,
    )


def get_jwks_client() -> PyJWKClient:
    if _jwks_client is None:
        raise RuntimeError(
            "El cliente JWKS no está inicializado (se crea al arrancar la aplicación)."
        )
    return _jwks_client


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=UNAUTHORIZED_DETAIL,
        headers={"WWW-Authenticate": "Bearer"},
    )


def auth_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=AUTH_UNAVAILABLE_DETAIL,
    )


def extract_bearer_token(credentials: HTTPAuthorizationCredentials | None) -> str:
    """Devuelve el token del encabezado Authorization o responde 401."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized()
    if not credentials.credentials:
        raise unauthorized()
    return credentials.credentials


def _check_audience(payload: dict[str, Any]) -> None:
    """Exige que aud o azp coincida con alguno de KEYCLOAK_AUDIENCE."""
    aud = payload.get("aud")
    token_audiences = {aud} if isinstance(aud, str) else set(aud or [])
    azp = payload.get("azp")
    if azp:
        token_audiences.add(azp)

    if not set(settings.keycloak_audiences).intersection(token_audiences):
        raise jwt.InvalidAudienceError("Audience o azp no coincide")


def verify_token(token: str) -> dict[str, Any]:
    """Valida firma RS256, iss, exp, sub y audiencia. Devuelve los claims.

    Responde 401 genérico si el token no es válido y 503 si el JWKS no responde.
    """
    try:
        signing_key = get_jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.keycloak_issuer,
            options={
                "require": ["exp", "iss", "sub"],
                "verify_aud": False,
            },
            leeway=TOKEN_LEEWAY_SECONDS,
        )
        _check_audience(payload)
        return payload
    except PyJWKClientConnectionError as exc:
        # Solo el tipo de la excepción: su mensaje puede incluir URLs internas.
        logger.error("No se pudo consultar el JWKS de Keycloak (%s).", type(exc).__name__)
        raise auth_unavailable() from exc
    except PyJWTError as exc:
        logger.warning("Token rechazado: %s", type(exc).__name__)
        raise unauthorized() from exc
    except Exception as exc:
        # Sin traceback ni mensaje: podrían exponer detalles internos o fragmentos del token.
        logger.error("Error inesperado al validar el token (%s).", type(exc).__name__)
        raise unauthorized() from exc


def get_realm_roles(claims: dict[str, Any]) -> set[str]:
    realm_access = claims.get("realm_access") or {}
    roles = realm_access.get("roles", [])
    return set(roles) if isinstance(roles, list) else set()


# TODO(keycloak-roles): sin uso por ahora, porque los roles se leen de la base de
# datos (tsgp_usuario_rol). Podrá usarse si más adelante los roles salen del token
# (realm_access.roles); en ese caso también puede reemplazar a UsuarioService.get_roles.
def require_realm_role(role: str):
    def role_checker(
        credentials: Annotated[
            HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
        ] = None,
    ) -> dict[str, Any]:
        claims = verify_token(extract_bearer_token(credentials))
        if role not in get_realm_roles(claims):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes el rol requerido",
            )
        return claims

    return role_checker
