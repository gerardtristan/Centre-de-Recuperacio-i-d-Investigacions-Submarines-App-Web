"""Rutes del 06 a l'àrea d'administració (M06-8): s'inclouen a `apps.accounts.admin_urls`, dins
de l'espai de noms `administration` (sessió d'administració i TOTP). Cap ruta pública."""

from django.urls import path

from . import confirm_views, views

urlpatterns = [
    # T-M06-24: pendents de confirmar (LC5).
    path(
        "llicencies/per-confirmar/", confirm_views.unconfirmed_view, name="licences_unconfirmed"
    ),  # fmt: skip
    path(
        "llicencies/<int:licence_id>/confirma/", confirm_views.confirm_view, name="licences_confirm"
    ),  # fmt: skip
    path("llicencies/", views.list_view, name="licences"),
    path("llicencies/exporta/", views.export_view, name="licences_export"),
    path("llicencies/preus/", views.prices_view, name="licences_prices"),
    path("llicencies/<int:licence_id>/tramita/", views.file_view, name="licences_file"),
    path("llicencies/<int:licence_id>/vigent/", views.activate_view, name="licences_activate"),
]
