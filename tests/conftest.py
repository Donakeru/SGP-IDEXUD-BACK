"""Configuración de pruebas: evita depender de una base de datos real."""

import os

# app.db crea el engine al importarse y exige estas variables; no se conecta.
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_NAME", "test")

# Settings valida el modo de autenticación al importarse. Las pruebas actuales
# no usan Keycloak, así que se ejecutan en modo dev.
os.environ.setdefault("AUTH_MODE", "dev")
os.environ.setdefault("ENVIRONMENT", "development")
