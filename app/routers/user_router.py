"""Endpoints relacionados con usuarios."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.roles import RolCodigo
from app.dependencies import get_authenticated_user, get_db, require_any_role
from app.models import Usuario
from app.schemas.rol import RolResponse
from app.schemas.usuario import UserResponse
from app.services.auth_service import get_user_roles
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/users", tags=["users"])


# Debe declararse antes de "/{id_usuario}" para que "me" no se interprete como id.
@router.get("/me", response_model=UserResponse)
def get_me(
    usuario: Usuario | None = Depends(get_authenticated_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Devuelve el usuario autenticado con sus roles.

    Responde 200 aunque el usuario esté inactivo o no tenga roles: así el front
    puede mostrar el estado real de la cuenta.
    """
    # TODO(dev-mode): eliminar el 404 junto con el modo dev.
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No disponible en modo dev",
        )

    return UserResponse(
        id_usuario=usuario.id_usuario,
        nombre=usuario.nombre,
        correo=usuario.correo,
        es_activo=usuario.es_activo,
        roles=[
            RolResponse(codigo=rol.codigo, nombre=rol.nombre)
            for rol in get_user_roles(db, usuario.id_usuario)
        ],
    )


# TODO(dev-mode): este endpoint existe para el login provisional del front. Eliminarlo
# (o reemplazarlo por /users/me) junto con el modo dev. Mientras tanto, en modo
# keycloak solo lo puede usar un administrador.
@router.get(
    "/{id_usuario}",
    response_model=UserResponse,
    dependencies=[Depends(require_any_role(RolCodigo.ADMINISTRADOR))],
)
def get_user_by_id(
    id_usuario: int,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Devuelve un usuario junto con sus roles."""
    user = UsuarioService(db).get_by_id(id_usuario)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    return UserResponse(
        id_usuario=user.id_usuario,
        nombre=user.nombre,
        correo=user.correo,
        es_activo=user.es_activo,
        roles=[
            RolResponse.model_validate(usuario_rol.rol)
            for usuario_rol in user.usuario_roles
            if usuario_rol.rol is not None
        ],
    )
