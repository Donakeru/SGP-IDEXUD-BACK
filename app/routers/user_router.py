from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.usuario import UserResponse
from app.schemas.rol import RolResponse
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/users", tags=["users"])

#, response_model=UserResponse
@router.get("/{id_usuario}")
def get_user_by_id(id_usuario: int, db: Session = Depends(get_db)):

    user = UsuarioService(db).get_by_id(id_usuario)

    print(user.usuario_roles[0].rol.codigo)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    return user
