"""Producció (VPS de Hetzner amb Coolify, darrere del proxy que acaba l'HTTPS)."""

from .base import *  # noqa: F403
from .base import env

DEBUG = False
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])
# Un salt: el proxy de Coolify. Si n'hi ha més (p. ex. una CDN), cal augmentar-ho.
NUM_PROXIES = env.int("DJANGO_NUM_PROXIES", default=1)

# El proxy de Coolify rep l'HTTPS i ho indica amb aquesta capçalera.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("DJANGO_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
# Enllaços dels correus sempre cap al domini de la plataforma, amb HTTPS (decisió 019).
PUBLIC_SITE_URL = env("PUBLIC_SITE_URL", default="https://cris1954.cat").rstrip("/")

# Claus del QR del carnet (079, RN-M01-85): pròpies i obligatòries; mai la derivada de proves.
CARD_QR_KEYS = env.list("CARD_QR_KEYS")
CARD_QR_ACTIVE_KEY = env("CARD_QR_ACTIVE_KEY")
CARD_QR_KEYS_REQUIRED = True

# Correu: el proveïdor real s'ha de declarar sencer; mai la bústia de proves local per defecte.
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)

# Fitxers privats a Scaleway Object Storage (París), un bucket privat per entorn (decisió 005).
# Que el bucket no es pugui llistar ni sigui públic es configura a Scaleway.
PRIVATE_FILES_LOCAL_ALLOWED = False
STORAGES = {
    **STORAGES,  # noqa: F405
    "private": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": env("S3_BUCKET_FITXERS"),
            "endpoint_url": env("S3_ENDPOINT_URL"),
            "region_name": env("S3_REGION", default="fr-par"),
            "access_key": env("S3_ACCESS_KEY_ID"),
            "secret_key": env("S3_SECRET_ACCESS_KEY"),
            "default_acl": "private",
            "querystring_auth": True,
            "querystring_expire": PRIVATE_FILES_SIGNED_URL_TTL,  # noqa: F405
            "file_overwrite": False,
            "signature_version": "s3v4",
        },
    },
}
