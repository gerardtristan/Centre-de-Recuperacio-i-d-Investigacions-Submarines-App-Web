"""Rutes públiques del 07 (M07-8; RN-M07-01): declarades una a una a `core/tests/test_access.py`.
Les d'administració (`/gestio/web/`) s'inclouran a `accounts/admin_urls.py` (torn del nucli)."""

from django.urls import path

from . import news_views, views

app_name = "website"

urlpatterns = [
    # T-M07-11: «no trobat» mentre `website.contact_enabled` és apagat (P-486).
    path("contacte/", views.contact_view, name="contact"),
    # T-M07-13: «no trobat» mentre `website.newsletter_enabled` és apagat (P-42); l'enllaç del
    # correu és la credencial de confirmar i de donar-se de baixa.
    path("butlleti/", views.newsletter_view, name="newsletter"),
    path(
        "butlleti/confirmar/<str:token>/",
        views.newsletter_confirm_view,
        name="newsletter_confirm",
    ),
    path(
        "butlleti/baixa/<str:token>/",
        views.newsletter_unsubscribe_view,
        name="newsletter_unsubscribe",
    ),
    # T-M07-08 (RN-M07-01 i 02): les notícies publicades, i les fotos de les pàgines i de les
    # notícies publicades (P-489), comprovades a cada petició.
    path("noticies/", news_views.public_list_view, name="news_list"),
    path("noticies/<slug:slug>/", news_views.public_detail_view, name="news_detail"),
    path("web/fotos/<uuid:key>/", news_views.media_view, name="media"),
    # T-M07-09 (RN-M07-12): les preguntes freqüents publicades i el cercador.
    path("ajuda/", news_views.help_view, name="help"),
]
