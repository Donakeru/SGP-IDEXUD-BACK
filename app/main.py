import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.security import init_jwks_client
from app.db import check_database_connection, close_database_connection
from app.routers import list_router, proposal_router, user_router

# Configuración de Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# Las sentencias SQL (con sus parámetros) solo se registran con SQL_ECHO=true en
# un entorno local; en cualquier otro caso el logger de SQLAlchemy queda en WARNING.
if not settings.sql_echo:
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


# Consulta de conexión con la BD
@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.legacy_auth_mode_defined:
        logger.warning("AUTH_MODE ya no existe y se ignora.")

    check_database_connection()
    init_jwks_client()
    logger.info("Autenticación Keycloak activa (emisor: %s)", settings.keycloak_issuer)

    yield
    close_database_connection()


# La documentación de la API solo se publica en development o local.
docs_enabled = settings.docs_enabled

app = FastAPI(
    title='SGP - IDEXUD',
    lifespan=lifespan,
    docs_url=f"{settings.app_subpath}/docs" if docs_enabled else None,
    redoc_url=f"{settings.app_subpath}/redoc" if docs_enabled else None,
    openapi_url=f"{settings.app_subpath}/openapi.json" if docs_enabled else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Router principal con prefijo global
api_router = APIRouter(prefix=settings.app_subpath)


@api_router.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Estado del servicio. Es público."""
    return {"status": "ok"}


api_router.include_router(user_router.router)
api_router.include_router(proposal_router.router)
api_router.include_router(list_router.router)

app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("main:app")
