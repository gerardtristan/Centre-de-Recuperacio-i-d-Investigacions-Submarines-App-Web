"""Urlconf de proves: el de la plataforma amb les rutes del 09 dins de l'espai de noms
`administration`, com quedarà quan el torn del nucli les inclogui a `apps.accounts.admin_urls`."""

from django.conf import settings
from django.urls import include, path

from apps.accounts import admin_urls
from config import urls as base

EXTRA_ADMIN = [
    path("", include("apps.expenses.admin_urls")),
]
admin = (admin_urls.urlpatterns + EXTRA_ADMIN, "administration")

urlpatterns = [
    path(f"{settings.ADMIN_URL_PATH}/", include(admin)),
    *base.urlpatterns[1:],
]
