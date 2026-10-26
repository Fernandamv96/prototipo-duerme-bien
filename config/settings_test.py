"""Configuración para pruebas automatizadas (pytest)."""
import os

os.environ.setdefault("SECRET_KEY", "clave-solo-para-pruebas-automatizadas")
os.environ.pop("DATABASE_URL", None)

from .settings import *  # noqa: E402,F401,F403

SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
