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

# Correu: el proveïdor real s'ha de declarar sencer; mai la bústia de proves local per defecte.
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
