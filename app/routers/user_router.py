"""Endpoints relacionados con usuarios."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import AuthenticatedUser, get_db
from app.schemas.rol import RolResponse
from app.schemas.usuario import UserResponse
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(
    usuario: AuthenticatedUser,
    db: Session = Depends(get_db),
) -> UserResponse:
    """Devuelve el usuario autenticado con sus roles.

    Responde 200 aunque el usuario esté inactivo o no tenga roles: así el front
    puede mostrar el estado real de la cuenta.
    """
    return UserResponse(
        id_usuario=usuario.id_usuario,
        nombre=usuario.nombre,
        correo=usuario.correo,
        es_activo=usuario.es_activo,
        roles=[
            RolResponse(codigo=rol.codigo, nombre=rol.nombre)
            for rol in UsuarioService(db).get_roles(usuario.id_usuario)
        ],
    )
