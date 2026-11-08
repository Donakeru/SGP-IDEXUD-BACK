import uvicorn
import logging
from fastapi import FastAPI, APIRouter
from app.routers import user_router, proposal_router, list_router
from app.db import check_database_connection, close_database_connection
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

# Configuración de Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


# Consulta de conexión con la BD
@asynccontextmanager
async def lifespan(app: FastAPI):
    check_database_connection()
    yield
    close_database_connection()


app = FastAPI(
    title='SGP - IDEXUD',
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

origins = [
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router principal con prefijo global
api_router = APIRouter(prefix="/api")

api_router.include_router(user_router.router)
api_router.include_router(proposal_router.router)
api_router.include_router(list_router.router)

app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("main:app")