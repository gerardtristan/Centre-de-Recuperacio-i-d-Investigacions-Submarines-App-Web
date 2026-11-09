"""Rutes públiques i de l'àrea de socis del M01. Les d'administració són a `admin_urls.py`."""

from django.urls import path

from .views import personal, personal_card, personal_requests, public, public_card

app_name = "members"

urlpatterns = [
    path("fer-se-soci/", public.join_view, name="join"),
    # Àrea del soci (compte personal, T-M01-16). Sessió obligatòria per defecte (RN-40).
    path("socis/perfil/", personal.profile_view, name="profile"),
    path("socis/quotes/", personal.fees_view, name="fees"),
    path("socis/quotes/<int:fee_id>/", personal.fee_detail_view, name="fee_detail"),
    path("socis/carnet/", personal_card.card_view, name="card"),  # T-M01-19
    # Verificació pública del carnet (T-M01-20, P15): ruta pública declarada (RN-40).
    path("carnet/verificar/<str:token>/", public_card.card_verify_view, name="card_verify"),
    # T-M01-17: sol·licituds de canvi de tipus i de baixa (P14).
    path("socis/canvi-tipus/", personal_requests.change_type_view, name="change_type"),
    path("socis/baixa/", personal_requests.leave_view, name="leave"),
]
