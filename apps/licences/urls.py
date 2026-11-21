"""Rutes públiques del 06 (T-M06-07). Les d'administració són a `admin_urls.py`."""

from django.urls import path

from . import views

app_name = "licences"

urlpatterns = [
    # Pública declarada (RN-40), només amb `licences.non_members_enabled` (RN-M06-03).
    path("llicencies/", views.public_view, name="public"),
]
