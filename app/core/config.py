from dataclasses import dataclass, field
from os import getenv
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=False)

AUTH_MODE_DEV = "dev"
AUTH_MODE_KEYCLOAK = "keycloak"
VALID_AUTH_MODES = (AUTH_MODE_DEV, AUTH_MODE_KEYCLOAK)

# TODO(dev-mode): el modo dev debe eliminarse antes de desplegar. Ver
# docs/spec/keycloak-backend/design.md, sección 3.
DEV_ALLOWED_ENVIRONMENTS = ("development", "local")

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


@dataclass(frozen=True)
class Settings:
    """Configuración cargada desde las variables en .env"""

    environment: str = getenv("ENVIRONMENT") or "development"
    environment_defined: bool = bool((getenv("ENVIRONMENT") or "").strip())
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
    auth_mode: str = field(
        default_factory=lambda: (getenv("AUTH_MODE") or AUTH_MODE_KEYCLOAK)
        .strip()
        .lower()
    )
    keycloak_url: str = field(
        default_factory=lambda: (getenv("KEYCLOAK_URL") or "").strip().rstrip("/")
    )
    keycloak_realm: str = field(
        default_factory=lambda: (getenv("KEYCLOAK_REALM") or "").strip()
    )
    keycloak_audiences: list[str] = field(
        default_factory=lambda: _split_csv(getenv("KEYCLOAK_AUDIENCE"))
    )

    def __post_init__(self) -> None:
        if self.auth_mode not in VALID_AUTH_MODES:
            raise RuntimeError(
                f"AUTH_MODE='{self.auth_mode}' no es válido. "
                f"Valores permitidos: {', '.join(VALID_AUTH_MODES)}."
            )

        if self.auth_mode == AUTH_MODE_DEV:
            allowed = ", ".join(DEV_ALLOWED_ENVIRONMENTS)
            if not self.environment_defined:
                raise RuntimeError(
                    "AUTH_MODE=dev deshabilita la autenticación y exige definir "
                    f"ENVIRONMENT explícitamente con uno de: {allowed}."
                )
            if self.environment.strip().lower() not in DEV_ALLOWED_ENVIRONMENTS:
                raise RuntimeError(
                    "AUTH_MODE=dev deshabilita la autenticación y solo se permite "
                    f"con ENVIRONMENT en: {allowed} "
                    f"(valor recibido: '{self.environment}')."
                )
            return

        required_values = {
            "KEYCLOAK_URL": self.keycloak_url,
            "KEYCLOAK_REALM": self.keycloak_realm,
            "KEYCLOAK_AUDIENCE": self.keycloak_audiences,
        }
        missing = [name for name, value in required_values.items() if not value]
        if missing:
            raise RuntimeError(
                "AUTH_MODE=keycloak requiere definir: "
                f"{', '.join(missing)}. Completa estas variables en .env o en el "
                "entorno, o usa AUTH_MODE=dev solo en desarrollo local."
            )

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
