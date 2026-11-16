"""Desenvolupament local. Mai amb dades reals de socis."""

from .base import *  # noqa: F403
from .base import env

DEBUG = env.bool("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Proveïdor de pagaments fals, sense xarxa (T-M05a-03).
PAYMENTS_PROVIDER = env("PAYMENTS_PROVIDER", default="fake")

# En local, les pantalles «En construcció» es veuen (T-DX-03).
SHOW_UNDER_CONSTRUCTION = env.bool("SHOW_UNDER_CONSTRUCTION", default=True)
