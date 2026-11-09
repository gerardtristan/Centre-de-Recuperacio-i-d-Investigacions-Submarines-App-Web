"""Rutes del M01 a l'àrea d'administració: s'inclouen a `apps.accounts.admin_urls`, dins de
l'espai de noms `administration` (sessió d'administració i TOTP)."""

from django.urls import path

from .views import admin

urlpatterns = [
    path("importacions/cluber/", admin.cluber_preview_view, name="cluber_preview"),
    path("socis/altes/nova/", admin.join_in_person_view, name="join_in_person"),
]
