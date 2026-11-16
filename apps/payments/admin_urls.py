"""Rutes del 05a a l'àrea d'administració: s'inclouen a `apps.accounts.admin_urls`, dins de
l'espai de noms `administration` (sessió d'administració i TOTP). Cap ruta pública."""

from django.urls import path

from . import admin_views

urlpatterns = [
    path("pagaments/mandats/", admin_views.mandates_view, name="payments_mandates"),
]
