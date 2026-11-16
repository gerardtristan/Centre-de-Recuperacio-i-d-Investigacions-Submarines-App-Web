"""Rutes de la 04 a l'àrea d'administració (M04-8): s'inclouen a `apps.accounts.admin_urls`,
dins de l'espai de noms `administration` (sessió d'administració i TOTP). Cap ruta pública."""

from django.urls import path

from . import views

urlpatterns = [
    path("tresoreria/", views.accounts_view, name="treasury_accounts"),
    path("tresoreria/moviments/", views.movements_view, name="treasury_movements"),
    path("tresoreria/revisar/", views.review_view, name="treasury_review"),
    path(
        "tresoreria/revisar/<int:line_id>/excloure/",
        views.exclude_view,
        name="treasury_exclude_line",
    ),
]
