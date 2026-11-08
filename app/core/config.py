from dataclasses import dataclass, field
from os import getenv
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=False)


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
