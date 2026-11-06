from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db

router = APIRouter(prefix="/proposal", tags=["proposal"])


# response_model=UserCreate
@router.post("/")
def create_new_proposal():
    return {"hola": "aaaaaaaaa"}