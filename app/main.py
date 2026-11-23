import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import AUTH_MODE_DEV, settings
from app.core.security import init_jwks_client
from app.db import check_database_connection, close_database_connection
from app.routers import list_router, proposal_router, user_router

# Configuración de Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# Consulta de conexión con la BD
@asynccontextmanager
async def lifespan(app: FastAPI):
    check_database_connection()

    if settings.auth_mode == AUTH_MODE_DEV:
        # TODO(dev-mode): eliminar el modo dev antes de desplegar.
        logger.warning("Autenticación deshabilitada: solo desarrollo")
    else:
        init_jwks_client()
        logger.info("Autenticación Keycloak activa (emisor: %s)", settings.keycloak_issuer)

    yield
    close_database_connection()


app = FastAPI(
    title='SGP - IDEXUD',
    lifespan=lifespan,
    docs_url=f"{settings.app_subpath}/docs",
    redoc_url=f"{settings.app_subpath}/redoc",
    openapi_url=f"{settings.app_subpath}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router principal con prefijo global
api_router = APIRouter(prefix=settings.app_subpath)


@api_router.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Estado del servicio. Es público e indica el modo de autenticación."""
    return {"status": "ok", "auth_mode": settings.auth_mode}


api_router.include_router(user_router.router)
api_router.include_router(proposal_router.router)
api_router.include_router(list_router.router)

app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("main:app")
