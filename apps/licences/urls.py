"""Rutes del 06 a l'àrea del soci (M06-8): `/socis/llicencia`. Exigeixen sessió (el middleware) i
l'objecte surt de la sessió."""

from django.urls import path

from . import personal_views

app_name = "licences"

urlpatterns = [path("socis/llicencia/", personal_views.mine_view, name="mine")]
