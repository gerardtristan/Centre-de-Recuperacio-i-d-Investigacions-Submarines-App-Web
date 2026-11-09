"""Rutes públiques i de l'àrea de socis del M01. Les d'administració són a `admin_urls.py`."""

from django.urls import path

from .views import public

app_name = "members"

urlpatterns = [
    path("fer-se-soci/", public.join_view, name="join"),
]
