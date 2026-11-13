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
    "apps.payments",
    "apps.treasury",
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
    # Importats de Cluber: acceptar les polítiques a la primera entrada (079, A-27; T-M01-25).
    "apps.members.policies.ImportedPoliciesMiddleware",
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
                # Menú de l'administració segons els permisos del compte (T-M01-46).
                "apps.accounts.navigation.admin_navigation",
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

# Pagaments (05a; decisió 043). Sense proveïdor configurat no es pot cobrar res. Amb l'entorn
# real («live»), cap cobrament sense PAYMENTS_LIVE_CHARGES_ALLOWED, que només s'activa al nivell 2
# amb l'autorització de la junta (RN-M05a-11; decisió 025).
PAYMENTS_PROVIDER = env("PAYMENTS_PROVIDER", default="")
PAYMENTS_ENVIRONMENT = env("PAYMENTS_ENVIRONMENT", default="sandbox")
PAYMENTS_LIVE_CHARGES_ALLOWED = env.bool("PAYMENTS_LIVE_CHARGES_ALLOWED", default=False)
# Decisió 092: el proveïdor i el banc ficticis no arrenquen on això és cert (producció, prod.py).
FAKE_INTEGRATIONS_FORBIDDEN = False

# Adreça pública de la plataforma, per als enllaços dels correus (verificació i recuperació):
# la cua no té cap petició d'on treure-la. Domini: decisió 019.
PUBLIC_SITE_URL = env("PUBLIC_SITE_URL", default="http://localhost:8000").rstrip("/")

# Claus de xifratge dels camps sensibles (Fernet). La primera xifra; totes desxifren.
FIELD_ENCRYPTION_KEYS = env.list("FIELD_ENCRYPTION_KEYS")

# Claus del QR del carnet (079, RN-M01-85; `apps/members/card_keys.py`): «identificador:clau»
# separades per comes, i l'identificador de la que es fa servir per emetre. Sense cap, en local
# i a les proves se'n deriva una de `SECRET_KEY`; producció les exigeix (prod.py).
CARD_QR_KEYS = env.list("CARD_QR_KEYS", default=[])
CARD_QR_ACTIVE_KEY = env("CARD_QR_ACTIVE_KEY", default="")
CARD_QR_KEYS_REQUIRED = False

# Proxies de confiança davant de Django: decideix d'on es llegeix l'IP d'origen
# per al límit d'intents (V-01). 0 = connexió directa.
NUM_PROXIES = env.int("DJANGO_NUM_PROXIES", default=0)

# Recordatoris de quota (T-M01-18; RN-M01-14, Q-061 de la 072): dies respecte al venciment, en
# ordre. Els negatius, abans; els positius, només si encara no s'ha pagat. La quota de renovació
# es genera el dia del primer recordatori. Configurable amb una llista separada per comes.
MEMBER_FEE_REMINDER_OFFSETS = tuple(
    sorted(env.list("MEMBER_FEE_REMINDER_OFFSETS", cast=int, default=[-15, -1, 0, 15, 30]))
)

# Formulari «Fer-se soci» (T-M01-13): llindars acceptats pel responsable com a valors inicials
# configurables (Q-040 de la 072, 09/11/2026).
# Per origen: com a màxim N sol·licituds en M minuts; en arribar-hi, limitat M minuts més. Per
# destinatari: com a màxim N rebuts en 24 hores. Els terminis no poden passar de 24 hores, el
# que es conserven les peticions (`apps/accounts/limits.py`, RETENTION).
JOIN_FORM_ORIGIN_MAX = env.int("JOIN_FORM_ORIGIN_MAX", default=5)
JOIN_FORM_ORIGIN_MINUTES = env.int("JOIN_FORM_ORIGIN_MINUTES", default=60)
JOIN_FORM_RECIPIENT_MAX_PER_DAY = env.int("JOIN_FORM_RECIPIENT_MAX_PER_DAY", default=3)

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
# Remitent: l'adreça del club, que també rep les respostes (decisió 085, I-2; substitueix el
# remitent sense bústia de cris1954.cat de la 019). Per enviar des de cris.es, el proveïdor de
# correu ha de tenir aquest domini autenticat (SPF i DKIM): condició de producció.
# El nom que es mostra es canvia amb la mateixa variable: "Nom <adreça>".
EMAIL_FROM_TRANSACCIONAL = env("EMAIL_FROM_TRANSACCIONAL", default="C.R.I.S. <cris@cris.es>")
# Anys que es conserven les dades bloquejades després del 31/12 de l'any de l'últim registre
# econòmic de la persona (CA-19.5; decisió 085, G-1). Passat el termini, es destrueixen.
LOCKED_DATA_RETENTION_YEARS = env.int("LOCKED_DATA_RETENTION_YEARS", default=6)
# NIF del club (decisió 085, J-6): surt al darrere del carnet. És una dada pública de l'entitat.
CLUB_TAX_ID = env("CLUB_TAX_ID", default="V08591042")
EMAIL_REPLY_TO = env("EMAIL_REPLY_TO", default="cris@cris.es")
DEFAULT_FROM_EMAIL = EMAIL_FROM_TRANSACCIONAL
SERVER_EMAIL = EMAIL_FROM_TRANSACCIONAL
# Intents d'enviament d'un correu abans de donar-lo per fallit (i esborrar-ne el cos).
EMAIL_MAX_ATTEMPTS = env.int("EMAIL_MAX_ATTEMPTS", default=5)
# Límit diari del proveïdor, sumant totes les categories (RN-A3), i la part que el butlletí no
# pot gastar perquè es reserva per als transaccionals (RN-A4, V-07). Els dies són en hora local.
EMAIL_DAILY_LIMIT = env.int("EMAIL_DAILY_LIMIT", default=300)
EMAIL_TRANSACTIONAL_RESERVE = env.int("EMAIL_TRANSACTIONAL_RESERVE", default=100)
# Un sol avís al dia quan els enviaments arriben a aquest percentatge del límit (RN-A6). El rep
# només l'administrador (decisió 081, punt 21). Aquí, per a desenvolupament i proves, no hi ha
# cap adreça per defecte i l'avís només queda al registre d'activitat; producció hi posa la del
# club (prod.py, decisió 084).
EMAIL_ALERT_THRESHOLD_PCT = env.int("EMAIL_ALERT_THRESHOLD_PCT", default=80)
EMAIL_ALERT_TO = env.list("EMAIL_ALERT_TO", default=[])

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
# Perfil del CSV de l'extracte bancari (T-M00-01). Supòsit fins que el banc doni una mostra
# anonimitzada (P-45 punt 10, S-M04-03; P-89): noms de les columnes de la capçalera (sense
# distingir majúscules; «balance» buit si no n'hi ha), separador, data i separador decimal.
BANK_STATEMENT_CSV_PROFILE = {
    "delimiter": ";",
    "date": "Data",
    "date_format": "%d/%m/%Y",
    "concept": "Concepte",
    "amount": "Import",
    "balance": "Saldo",
    "decimal": ",",
}
# Dies que es conserva una exportació RGPD abans d'esborrar-la (V-08).
GDPR_EXPORT_RETENTION_DAYS = env.int("GDPR_EXPORT_RETENTION_DAYS", default=7)

STATIC_URL = "/static/"
# Els logotips es serveixen des d'assets/marca/, sense una segona còpia (T-M01-38).
STATICFILES_DIRS = [BASE_DIR / "static", ("marca", BASE_DIR / "assets" / "marca")]
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
