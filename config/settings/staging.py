"""Servidor de proves (decisions 090 i 099; docs/guies/servidor-de-proves-al-portatil.md).
Mai amb dades reals.

Es comporta com producció (DEBUG apagat, cookies segures), però amb les integracions fictícies:
el proveïdor de pagaments fals en mode de proves (092), el correu a la bústia de proves (Mailpit),
que no envia res cap a fora, i els fitxers privats al disc. Corre al portàtil del propietari amb
Docker; l'HTTPS el fa el túnel (Cloudflare Tunnel o Tailscale), al davant hi ha una contrasenya
(Caddy) i cap cercador no l'indexa.
"""

from .base import *  # noqa: F403
from .base import env

DEBUG = False
# Les adreces dels túnels (l'aleatòria de Cloudflare canvia a cada arrencada) i el mateix portàtil.
ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1", ".trycloudflare.com", ".ts.net"]
)
CSRF_TRUSTED_ORIGINS = env.list(
    "DJANGO_CSRF_TRUSTED_ORIGINS", default=["https://*.trycloudflare.com", "https://*.ts.net"]
)
# Dos salts: el túnel i el Caddy.
NUM_PROXIES = env.int("DJANGO_NUM_PROXIES", default=2)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# El túnel ja serveix només HTTPS; des del portàtil s'hi entra per http://localhost:8080, que els
# navegadors tracten com a segur (les cookies segures hi funcionen).
SECURE_SSL_REDIRECT = env.bool("DJANGO_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# Sense HSTS: les adreces són provisionals i no s'han de quedar fixades als navegadors.
SECURE_HSTS_SECONDS = env.int("DJANGO_HSTS_SECONDS", default=0)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
# La salut (`/salut/`) la consulta Docker mateix per HTTP, sense passar pel Caddy.
SECURE_REDIRECT_EXEMPT = [r"^salut/$"]

# Integracions fictícies (092): el proveïdor fals, sempre en mode de proves i sense cobraments.
FAKE_INTEGRATIONS_FORBIDDEN = False
PAYMENTS_PROVIDER = "fake"
PAYMENTS_ENVIRONMENT = "sandbox"
PAYMENTS_LIVE_CHARGES_ALLOWED = False

# Correu: la bústia de proves (servei «mailpit» del docker-compose). Cap correu surt.
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
