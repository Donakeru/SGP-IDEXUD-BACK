"""Configuración de pruebas: evita depender de una base de datos real."""

import os

# app.db crea el engine al importarse y exige estas variables; no se conecta.
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_NAME", "test")
