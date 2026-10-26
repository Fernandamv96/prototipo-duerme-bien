"""
Configuración del proyecto Django - Sistema de Gestión de Pasajeros y Habitaciones,
Hotel "Duerme Bien" (Unidad 3, Ingeniería de Software - INACAP).

No se usa django.contrib.admin ni django.contrib.auth: el caso define exactamente dos roles
(Administrador, Encargado de Hotel) con un panel propio (módulo 'cuentas'), por lo que se evita
el panel genérico de Django y su modelo de usuario para no duplicar conceptos ni abrir una
superficie de acceso adicional no contemplada en el caso.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: en producción, definir SECRET_KEY por variable de entorno.
# En el entorno de producción de Vercel no hay valor por defecto: sin la variable,
# la app no arranca (así nunca se firma una sesión con una clave publicada en el repo).
SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    if os.environ.get("VERCEL_ENV") == "production":
        from django.core.exceptions import ImproperlyConfigured

        raise ImproperlyConfigured("Falta la variable de entorno SECRET_KEY.")
    SECRET_KEY = "django-insecure-solo-para-desarrollo-local-cambiar-en-produccion"

# Vercel define VERCEL=1 en sus funciones: ahí se asume producción por defecto.
EN_VERCEL = os.environ.get("VERCEL") == "1"

# DEBUG debe ser False en producción (PS-07 / SEG-07: no exponer detalles técnicos).
DEBUG = os.environ.get("DJANGO_DEBUG", "0" if EN_VERCEL else "1") == "1"

if not DEBUG and SECRET_KEY.startswith("django-insecure"):
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("Defina SECRET_KEY por variable de entorno antes de ejecutar en producción.")

_hosts_por_defecto = ".vercel.app" if EN_VERCEL else "127.0.0.1,localhost"
ALLOWED_HOSTS = [h for h in os.environ.get("ALLOWED_HOSTS", _hosts_por_defecto).split(",") if h]
# Vercel (PaaS) informa el dominio del despliegue en VERCEL_URL.
if os.environ.get("VERCEL_URL"):
    ALLOWED_HOSTS.append(os.environ["VERCEL_URL"])
CSRF_TRUSTED_ORIGINS = ["https://*.vercel.app"] + [
    f"https://{h}" for h in ALLOWED_HOSTS if h not in ("127.0.0.1", "localhost") and not h.startswith(".")
]


INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "hotel.cuentas",
    "hotel.habitaciones",
    "hotel.pasajeros",
    "hotel.reportes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",                  # sirve /static/ en producción
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",       # OWASP: cabecera CSP nativa (Django 6)
    "hotel.cuentas.seguridad.SesionUsuarioMiddleware",              # sesión propia + expiración (SEG-06)
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Base de datos: SQLite en desarrollo, PostgreSQL en producción (sección 8.1 del informe).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
if os.environ.get("DATABASE_URL"):
    import dj_database_url
    DATABASES["default"] = dj_database_url.parse(os.environ["DATABASE_URL"], conn_max_age=600)


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"   # destino de collectstatic (producción)
WHITENOISE_USE_FINDERS = True            # en Vercel sirve los estáticos de cada app sin collectstatic
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

from django.contrib.messages import constants as message_constants  # noqa: E402

MESSAGE_TAGS = {
    message_constants.ERROR: "danger",   # para que coincida con las clases de Bootstrap
}

# ------------------------------------------------------------------ sesión y cookies (OWASP / ISO 27002)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "1") == "1"   # exige HTTPS en producción
SESSION_COOKIE_AGE = 15 * 60                                          # 15 min (SEG-06)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
CSRF_COOKIE_HTTPONLY = True

# ------------------------------------------------------------------ cabeceras de seguridad (OWASP / SEG-09)
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
if EN_VERCEL:
    # Vercel termina TLS en su proxy; sin esto Django cree que la petición es HTTP y la
    # redirección a HTTPS entra en un ciclo infinito.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

SECURE_CSP = {
    "default-src": ["'self'"],
    "style-src": ["'self'", "https://cdn.jsdelivr.net"],
    "script-src": ["'self'"],
    "font-src": ["'self'", "https://cdn.jsdelivr.net"],   # tipografía Plus Jakarta Sans (@fontsource)
    "frame-ancestors": ["'none'"],
}

# ------------------------------------------------------------------ logging (RNF-09: no exponer detalles)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
