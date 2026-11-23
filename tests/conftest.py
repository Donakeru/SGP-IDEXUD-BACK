"""Configuración de pruebas: evita depender de una base de datos o de Keycloak reales."""

import os

import pytest

# app.db crea el engine al importarse y exige estas variables; no se conecta.
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_NAME", "test")

# Settings exige las variables de Keycloak al importarse. Son valores ficticios: las
# pruebas reemplazan la autenticación con dependency_overrides y no llaman a Keycloak.
os.environ.setdefault("KEYCLOAK_URL", "http://keycloak.test")
os.environ.setdefault("KEYCLOAK_REALM", "test")
os.environ.setdefault("KEYCLOAK_AUDIENCE", "test")


@pytest.fixture(autouse=True)
def authenticated_principal():
    """Simula un usuario autenticado con rol operativo (dependency_overrides)."""
    from app.core.principal import Principal
    from app.dependencies import get_current_principal
    from app.main import app

    app.dependency_overrides[get_current_principal] = lambda: Principal(
        id_usuario=1,
        nombre="Usuario de prueba",
        correo="prueba@example.com",
        es_activo=True,
        roles=frozenset({"administrador"}),
    )
    yield
    app.dependency_overrides.pop(get_current_principal, None)
