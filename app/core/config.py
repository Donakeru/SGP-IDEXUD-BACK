from dataclasses import dataclass, field
from os import environ, getenv
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=False)

# Entornos donde se publica la documentación de la API (/docs, /redoc, /openapi.json)
# y donde se permite el eco de SQL. En cualquier otro valor quedan desactivados.
LOCAL_ENVIRONMENTS = ("development", "local")

DEFAULT_APP_SUBPATH = "/api"
DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://localhost:3000"


def _normalize_subpath(raw: str | None) -> str:
    """Devuelve "" o "/xxx". Sin definir usa "/api"; definido y vacío, la raíz."""
    if raw is None:
        return DEFAULT_APP_SUBPATH
    cleaned = raw.strip().strip("/")
    return f"/{cleaned}" if cleaned else ""


def _split_csv(raw: str | None) -> list[str]:
    return [item.strip() for item in (raw or "").split(",") if item.strip()]


def _read_cors_origins() -> list[str]:
    raw = getenv("CORS_ORIGINS")
    return _split_csv(raw if raw is not None else DEFAULT_CORS_ORIGINS)


def _is_true(raw: str | None) -> bool:
    return (raw or "").strip().lower() in ("1", "true", "yes", "si", "sí")


@dataclass(frozen=True)
class Settings:
    """Configuración cargada desde las variables en .env"""

    environment: str = getenv("ENVIRONMENT") or "development"
    db_user: str = getenv("DB_USER", "")
    db_password: str = field(default=getenv("DB_PASSWORD", ""), repr=False)
    db_host: str = getenv("DB_HOST") or "localhost"
    db_port: int = int(getenv("DB_PORT") or "5432")
    db_name: str = getenv("DB_NAME", "")
    storage_root: Path = field(
        default_factory=lambda: PROJECT_ROOT / (getenv("STORAGE_ROOT") or "storages")
    )
    max_upload_size_mb: int = int(getenv("MAX_UPLOAD_SIZE_MB") or "10")
    app_subpath: str = field(
        default_factory=lambda: _normalize_subpath(getenv("APP_SUBPATH"))
    )
    cors_origins: list[str] = field(default_factory=_read_cors_origins)
    keycloak_url: str = field(
        default_factory=lambda: (getenv("KEYCLOAK_URL") or "").strip().rstrip("/")
    )
    keycloak_realm: str = field(
        default_factory=lambda: (getenv("KEYCLOAK_REALM") or "").strip()
    )
    keycloak_audiences: list[str] = field(
        default_factory=lambda: _split_csv(getenv("KEYCLOAK_AUDIENCE"))
    )
    sql_echo_requested: bool = field(
        default_factory=lambda: _is_true(getenv("SQL_ECHO"))
    )
    # AUTH_MODE ya no existe; si el entorno aún lo define, main.py avisa una vez.
    legacy_auth_mode_defined: bool = field(
        default_factory=lambda: "AUTH_MODE" in environ
    )

    def __post_init__(self) -> None:
        required_values = {
            "KEYCLOAK_URL": self.keycloak_url,
            "KEYCLOAK_REALM": self.keycloak_realm,
            "KEYCLOAK_AUDIENCE": self.keycloak_audiences,
        }
        missing = [name for name, value in required_values.items() if not value]
        if missing:
            raise RuntimeError(
                f"Faltan variables de Keycloak: {', '.join(missing)}. "
                "Completa estas variables en .env o en el entorno."
            )

    @property
    def is_local_environment(self) -> bool:
        return self.environment.strip().lower() in LOCAL_ENVIRONMENTS

    @property
    def docs_enabled(self) -> bool:
        """La documentación de la API solo se publica en development o local."""
        return self.is_local_environment

    @property
    def sql_echo(self) -> bool:
        """El eco de SQL (incluye parámetros) exige entorno local y SQL_ECHO=true."""
        return self.sql_echo_requested and self.is_local_environment

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def keycloak_issuer(self) -> str:
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}"

    @property
    def keycloak_jwks_url(self) -> str:
        return f"{self.keycloak_issuer}/protocol/openid-connect/certs"

    def get_database_url(self) -> URL:

        required_values = {
            "DB_USER": self.db_user,
            "DB_PASSWORD": self.db_password,
            "DB_NAME": self.db_name,
        }

        # verificar si hacen falta datos para la conexión
        missing_values = [name for name, value in required_values.items() if not value]
        if missing_values:
            missing = ", ".join(missing_values)
            raise RuntimeError(
                f"Faltan variables de conexión a PostgreSQL: {missing}. "
                "Completa las variables DB_* en .env o en el entorno."
            )

        return URL.create(
            drivername="postgresql+psycopg",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )


settings = Settings()
