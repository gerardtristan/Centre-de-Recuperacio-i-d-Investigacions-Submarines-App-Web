"""Entorn de proves temporal (decisió 090; docs/entorn-de-proves.md). Mai amb dades reals.

Es comporta com producció (DEBUG apagat, HTTPS, cookies segures), però amb les integracions
fictícies: el proveïdor de pagaments fals en mode de proves (092), el correu a la bústia de proves
del mateix servidor (Mailpit), que no envia res cap a fora, i els fitxers privats al disc del
servidor. Al davant hi ha una contrasenya (Caddy) i cap cercador no l'indexa.
"""

from .base import *  # noqa: F403
from .base import env

DEBUG = False
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])
# Un salt: el Caddy del servidor de proves, que acaba l'HTTPS.
NUM_PROXIES = env.int("DJANGO_NUM_PROXIES", default=1)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# Una hora: l'adreça és provisional i no s'ha de quedar fixada als navegadors.
SECURE_HSTS_SECONDS = env.int("DJANGO_HSTS_SECONDS", default=3600)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
# La salut (`/salut/`) la consulta el servidor mateix per HTTP, sense passar pel Caddy.
SECURE_REDIRECT_EXEMPT = [r"^salut/$"]

# Integracions fictícies (092): el proveïdor fals, sempre en mode de proves i sense cobraments.
FAKE_INTEGRATIONS_FORBIDDEN = False
PAYMENTS_PROVIDER = "fake"
PAYMENTS_ENVIRONMENT = "sandbox"
PAYMENTS_LIVE_CHARGES_ALLOWED = False

# Correu: la bústia de proves del servidor (servei «mailpit» del docker-compose). Cap correu surt.
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="mailpit")
EMAIL_PORT = env.int("EMAIL_PORT", default=1025)
EMAIL_HOST_USER = ""
EMAIL_HOST_PASSWORD = ""
EMAIL_USE_TLS = False

# Pantalles «En construcció» i signatura del mandat amb el text d'esborrany, com en local.
SHOW_UNDER_CONSTRUCTION = env.bool("SHOW_UNDER_CONSTRUCTION", default=True)
MANDATE_SIGNING_ENABLED = env.bool("MANDATE_SIGNING_ENABLED", default=True)

# Dades inventades al servidor de proves: `seed_demo_data` amb la base del docker-compose («db»)
# i el secret TOTP generat al servidor (el de prova continua refusat sense DEBUG, RN-M01-84).
DEMO_DATA_ALLOWED = True
DEMO_DATA_DB_HOSTS = ["db"]
STAGING_TOTP_SECRET = env("STAGING_TOTP_SECRET", default="")

LOGGING = {
    **LOGGING,  # noqa: F405
    "root": {"handlers": ["console"], "level": "WARNING"},
}
