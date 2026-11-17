"""Rutes de la 04 a l'àrea d'administració (M04-8): s'inclouen a `apps.accounts.admin_urls`,
dins de l'espai de noms `administration` (sessió d'administració i TOTP). Cap ruta pública."""

from django.urls import path

from . import views

urlpatterns = [
    path("tresoreria/", views.accounts_view, name="treasury_accounts"),
    path("tresoreria/moviments/", views.movements_view, name="treasury_movements"),
    path("tresoreria/moviments/exporta/", views.export_view, name="treasury_export"),
    path("tresoreria/conciliacio/", views.reconciliation_view, name="treasury_reconciliation"),
    path(
        "tresoreria/conciliacio/<int:line_id>/confirma/",
        views.confirm_view,
        name="treasury_confirm_line",
    ),
    path(
        "tresoreria/conciliacio/desfes/<int:reconciliation_id>/",
        views.undo_view,
        name="treasury_undo_reconciliation",
    ),
    path("tresoreria/revisar/", views.review_view, name="treasury_review"),
    path(
        "tresoreria/revisar/<int:line_id>/excloure/",
        views.exclude_view,
        name="treasury_exclude_line",
    ),
]
