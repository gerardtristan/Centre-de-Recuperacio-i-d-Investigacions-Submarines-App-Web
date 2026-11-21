"""Rutes del 06 a l'àrea d'administració (M06-8): s'inclouen a `apps.accounts.admin_urls`, dins
de l'espai de noms `administration` (sessió d'administració i TOTP). Cap ruta pública."""

from django.urls import path

from . import views

urlpatterns = [
    path("llicencies/", views.list_view, name="licences"),
    path("llicencies/exporta/", views.export_view, name="licences_export"),
    path("llicencies/preus/", views.prices_view, name="licences_prices"),
    path("llicencies/<int:licence_id>/tramita/", views.file_view, name="licences_file"),
    path("llicencies/<int:licence_id>/vigent/", views.activate_view, name="licences_activate"),
]
