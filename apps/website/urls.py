"""Rutes públiques del 07 (M07-8; RN-M07-01): declarades una a una a `core/tests/test_access.py`.
Les d'administració (`/gestio/web/`) s'inclouran a `accounts/admin_urls.py` (torn del nucli)."""

from django.urls import path

from . import views

app_name = "website"

urlpatterns = [
    # T-M07-11: «no trobat» mentre `website.contact_enabled` és apagat (P-486).
    path("contacte/", views.contact_view, name="contact"),
]
