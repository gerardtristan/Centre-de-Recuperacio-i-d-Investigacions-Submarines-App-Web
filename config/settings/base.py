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
    # Cua de tasques sobre PostgreSQL (decisió 012). Abans de les apps que hi registren tasques.
    "procrastinate.contrib.django",
    "apps.core",
    "apps.accounts",
    "apps.members",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # Després de la sessió i abans de Common (decisió 061).
    "django.middleware.locale.LocaleMiddleware",
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
                "django.template.context_processors.i18n",
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

# Adreça pública de la plataforma, per als enllaços dels correus (verificació i recuperació):
# la cua no té cap petició d'on treure-la. Domini: decisió 019.
PUBLIC_SITE_URL = env("PUBLIC_SITE_URL", default="http://localhost:8000").rstrip("/")

# Claus de xifratge dels camps sensibles (Fernet). La primera xifra; totes desxifren.
FIELD_ENCRYPTION_KEYS = env.list("FIELD_ENCRYPTION_KEYS")

# Proxies de confiança davant de Django: decideix d'on es llegeix l'IP d'origen
# per al límit d'intents (V-01). 0 = connexió directa.
NUM_PROXIES = env.int("DJANGO_NUM_PROXIES", default=0)

# Decisió 061: el català és l'única llengua activa i la de reserva. No s'hi afegeix cap llengua
# sense les seves traduccions revisades (P-49).
LANGUAGE_CODE = "ca"
LANGUAGES = [("ca", "Català")]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True

# Correu (annex A de la spec 00; decisions 004, 019 i 042). El transport és SMTP estàndard, que
# ofereixen tant Brevo com Scaleway Transactional Email: canviar de proveïdor és canviar aquestes
# variables. Les credencials només surten de l'entorn. Per defecte, la bústia de proves local
# (Mailpit al port 1025); producció les exigeix totes.
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=1025)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=30)
# Remitent sense bústia real a cris1954.cat, amb resposta a l'adreça del club (decisió 019).
# El nom que es mostra es canvia amb la mateixa variable: "Nom <adreça>".
EMAIL_FROM_TRANSACCIONAL = env(
    "EMAIL_FROM_TRANSACCIONAL", default="C.R.I.S. <no-respon@cris1954.cat>"
)
EMAIL_REPLY_TO = env("EMAIL_REPLY_TO", default="cris@cris.es")
DEFAULT_FROM_EMAIL = EMAIL_FROM_TRANSACCIONAL
SERVER_EMAIL = EMAIL_FROM_TRANSACCIONAL
# Intents d'enviament d'un correu abans de donar-lo per fallit (i esborrar-ne el cos).
EMAIL_MAX_ATTEMPTS = env.int("EMAIL_MAX_ATTEMPTS", default=5)

# Fitxers privats (annex B de la spec 00; decisió 005; V-08). Fora de producció, un
# emmagatzematge local que imita Scaleway; producció hi posa Scaleway (prod.py).
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    "private": {
        "BACKEND": "apps.core.files.LocalSignedStorage",
        "OPTIONS": {"location": BASE_DIR / "var" / "fitxers-privats"},
    },
}
PRIVATE_FILES_LOCAL_ALLOWED = True
# Durada de les URL signades: 5 minuts (V-08).
PRIVATE_FILES_SIGNED_URL_TTL = env.int("S3_SIGNED_URL_TTL_SECONDS", default=300)
# Mida màxima d'un fitxer pujat: 10 MB (V-08 de la spec 00; la checklist C10 només demana
# que estigui limitada).
UPLOAD_MAX_BYTES = env.int("UPLOAD_MAX_BYTES", default=10 * 1024 * 1024)
# Dies que es conserva una exportació RGPD abans d'esborrar-la (V-08).
GDPR_EXPORT_RETENTION_DAYS = env.int("GDPR_EXPORT_RETENTION_DAYS", default=7)

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
