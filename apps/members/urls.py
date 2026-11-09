"""Rutes públiques i de l'àrea de socis del M01. Les d'administració són a `admin_urls.py`."""

from django.urls import path

from .views import personal, personal_card, public

app_name = "members"

urlpatterns = [
    path("fer-se-soci/", public.join_view, name="join"),
    # Àrea del soci (compte personal, T-M01-16). Sessió obligatòria per defecte (RN-40).
    path("socis/perfil/", personal.profile_view, name="profile"),
    path("socis/quotes/", personal.fees_view, name="fees"),
    path("socis/quotes/<int:fee_id>/", personal.fee_detail_view, name="fee_detail"),
    path("socis/carnet/", personal_card.card_view, name="card"),  # T-M01-19
]
