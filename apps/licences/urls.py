"""Rutes del 06 fora de l'administració (M06-8). L'àrea del soci, `/socis/llicencia`, exigeix
sessió (el middleware) i l'objecte surt de la sessió. La pàgina pública per a no socis (T-M06-07)
és declarada pública. Les d'administració són a `admin_urls.py`."""

from django.urls import path

from . import guest_views, personal_views, views

app_name = "licences"

urlpatterns = [
    path("socis/llicencia/", personal_views.mine_view, name="mine"),
    # Pública declarada (RN-40), només amb `licences.non_members_enabled` (RN-M06-03).
    path("llicencies/", views.public_view, name="public"),
    path("llicencies/demana/", guest_views.guest_request_view, name="guest_request"),
]
