"""Configuració comuna a tots els entorns.

Tots els valors sensibles surten de variables d'entorn (o d'un fitxer .env local,
que mai va al repositori). Vegeu .env.example.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core",
    "apps.accounts",
    "apps.members",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Tota vista exigeix sessió; les públiques es declaren amb @login_not_required.
    "apps.accounts.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Una sola base de dades PostgreSQL. Format: postgres://usuari:contrasenya@host:port/nom
DATABASES = {"default": env.db("DATABASE_URL")}

# Compte personal o d'administrador, lligat al perfil únic de la persona (spec 00, RN-11).
AUTH_USER_MODEL = "accounts.Account"

# V-01: mínim 12 caràcters; es rebutgen les habituals i les semblants a l'identificador.
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        "OPTIONS": {"user_attributes": ("login", "notification_email")},
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "accounts:login"

# Entrada d'administració separada, en una ruta discreta (arquitectura §5).
ADMIN_URL_PATH = env("ADMIN_URL_PATH", default="gestio").strip("/")
TOTP_ISSUER_NAME = env("TOTP_ISSUER_NAME", default="C.R.I.S.")

# Claus de xifratge dels camps sensibles (Fernet). La primera xifra; totes desxifren.
FIELD_ENCRYPTION_KEYS = env.list("FIELD_ENCRYPTION_KEYS")

# Proxies de confiança davant de Django: decideix d'on es llegeix l'IP d'origen
# per al límit d'intents (V-01). 0 = connexió directa.
NUM_PROXIES = env.int("DJANGO_NUM_PROXIES", default=0)

LANGUAGE_CODE = "ca"
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"

# Esdeveniments de seguretat (entrades, bloquejos). Fins a la T-M01-07 només van al registre
# del servidor; mai hi surten contrasenyes, codis ni secrets.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"cris.security": {"handlers": ["console"], "level": "INFO"}},
}
