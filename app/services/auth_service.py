"""Resolución del usuario local a partir de un token de Keycloak."""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    EmailAlreadyLinkedError,
    EmailNotVerifiedError,
    InvalidTokenSubjectError,
    TokenEmailMissingError,
    UserResolutionError,
)
from app.models import Rol, Usuario
from app.repositories import UsuarioRepository

logger = logging.getLogger(__name__)

MAX_RESOLUTION_ATTEMPTS = 3


def get_user_roles(db: Session, id_usuario: int) -> list[Rol]:
    """Devuelve los roles del usuario. Único punto de lectura de roles.

    TODO(keycloak-roles): puede reemplazarse por los roles de realm del token
    (claim realm_access.roles) si más adelante los roles salen de Keycloak.
    """
    return UsuarioRepository(db).get_roles(id_usuario)


class AuthService:
    """Busca, vincula o crea el usuario local que corresponde a un token."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.usuario_repository = UsuarioRepository(db)

    def resolve_user(self, claims: dict[str, Any]) -> Usuario:
        """Devuelve el usuario local del token, sin verificar estado ni roles."""
        sub = self._parse_sub(claims)

        for attempt in range(1, MAX_RESOLUTION_ATTEMPTS + 1):
            usuario = self.usuario_repository.get_by_keycloak_sub(sub)
            if usuario is not None:
                return usuario

            email = self._read_verified_email(claims)
            try:
                usuario = self._link_or_create(sub, email, claims)
            except IntegrityError:
                # Otra petición creó o vinculó al usuario a la vez: se vuelve a consultar.
                self.db.rollback()
                logger.info(
                    "Carrera al resolver usuario (intento %s/%s); se reintenta.",
                    attempt,
                    MAX_RESOLUTION_ATTEMPTS,
                )
                continue

            if usuario is not None:
                return usuario

        raise UserResolutionError("No se pudo resolver el usuario local.")

    @staticmethod
    def _parse_sub(claims: dict[str, Any]) -> UUID:
        raw_sub = claims.get("sub")
        if not isinstance(raw_sub, str):
            raise InvalidTokenSubjectError("El claim sub no es texto.")
        try:
            return UUID(raw_sub)
        except ValueError as exc:
            raise InvalidTokenSubjectError("El claim sub no es un UUID.") from exc

    @staticmethod
    def _read_verified_email(claims: dict[str, Any]) -> str:
        raw_email = claims.get("email")
        email = raw_email.strip().lower() if isinstance(raw_email, str) else ""
        if not email:
            raise TokenEmailMissingError("El token no incluye email.")
        if claims.get("email_verified") is not True:
            raise EmailNotVerifiedError("El correo no está verificado.")
        return email

    def _link_or_create(
        self,
        sub: UUID,
        email: str,
        claims: dict[str, Any],
    ) -> Usuario | None:
        """Vincula al usuario existente por correo o crea uno nuevo.

        Devuelve None si otra petición vinculó al usuario antes (hay que repetir).
        """
        existente = self.usuario_repository.get_by_correo(email)

        if existente is not None:
            if existente.keycloak_sub is not None and existente.keycloak_sub != sub:
                raise EmailAlreadyLinkedError("El correo pertenece a otra cuenta.")
            if existente.keycloak_sub == sub:
                return existente

            with self.db.begin_nested():
                linked = self.usuario_repository.link_keycloak_sub(
                    existente.id_usuario, sub
                )
            if not linked:
                self.db.rollback()
                return None
            self.db.commit()
            self.db.refresh(existente)
            return existente

        with self.db.begin_nested():
            usuario = self.usuario_repository.add(
                {
                    "nombre": self._build_name(claims, email),
                    "correo": email,
                    "keycloak_sub": sub,
                }
            )
            self.db.flush()
        self.db.commit()
        return usuario

    @staticmethod
    def _build_name(claims: dict[str, Any], email: str) -> str:
        def clean(value: Any) -> str:
            return value.strip() if isinstance(value, str) else ""

        name = clean(claims.get("name"))
        if name:
            return name

        full_name = " ".join(
            part
            for part in (clean(claims.get("given_name")), clean(claims.get("family_name")))
            if part
        )
        if full_name:
            return full_name

        return clean(claims.get("preferred_username")) or email
