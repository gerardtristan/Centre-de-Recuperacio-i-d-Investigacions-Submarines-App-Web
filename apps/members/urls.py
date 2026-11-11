"""Rutes públiques i de l'àrea de socis del M01. Les d'administració són a `admin_urls.py`."""

from django.urls import path

from .views import personal, personal_card, personal_requests, public, public_card

app_name = "members"

urlpatterns = [
    path("fer-se-soci/", public.join_view, name="join"),
    # Àrea del soci (compte personal, T-M01-16). Sessió obligatòria per defecte (RN-40).
    path("socis/perfil/", personal.profile_view, name="profile"),
    # T-M01-36: el soci declara la caducitat desconeguda d'una llicència seva (RN-M01-77).
    path(
        "socis/perfil/llicencia/<int:record_id>/",
        personal.declare_expiry_view,
        name="declare_expiry",
    ),
    # T-M01-16 (074): consentiments opcionals (Q-031) i canvi del correu d'entrada (RN-M01-79).
    path("socis/perfil/consentiment/", personal.consent_view, name="consent"),
    path("socis/perfil/correu/", personal.change_email_view, name="change_email"),
    # T-M01-22, peça mínima (074): sol·licitud d'esborrat (RN-M01-57, CA-M01-46).
    path("socis/perfil/esborrar/", personal.erase_view, name="erase"),
    path("socis/quotes/", personal.fees_view, name="fees"),
    path("socis/quotes/<int:fee_id>/", personal.fee_detail_view, name="fee_detail"),
    path("socis/carnet/", personal_card.card_view, name="card"),  # T-M01-19
    # Verificació pública del carnet (T-M01-20, P15): ruta pública declarada (RN-40).
    path("carnet/verificar/<str:token>/", public_card.card_verify_view, name="card_verify"),
    # T-M01-17: sol·licituds de canvi de tipus i de baixa (P14).
    path("socis/canvi-tipus/", personal_requests.change_type_view, name="change_type"),
    # T-M01-42 (073, RN-M01-93): el soci retira el seu pas a simpatitzant pendent. Només POST.
    path(
        "socis/canvi-tipus/retira/",
        personal_requests.change_type_withdraw_view,
        name="change_type_withdraw",
    ),
    path("socis/baixa/", personal_requests.leave_view, name="leave"),
]
