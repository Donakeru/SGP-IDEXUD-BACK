"""Endpoints relacionados con usuarios."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.rol import RolResponse
from app.schemas.usuario import UserResponse
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{id_usuario}", response_model=UserResponse)
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
        nombre=user.nombre,
        correo=user.correo,
        roles=[
            RolResponse.model_validate(usuario_rol.rol)
            for usuario_rol in user.usuario_roles
            if usuario_rol.rol is not None
        ],
    )
