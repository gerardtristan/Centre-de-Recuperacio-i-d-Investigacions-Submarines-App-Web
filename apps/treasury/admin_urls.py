"""Rutes de la 04 a l'àrea d'administració (M04-8): s'inclouen a `apps.accounts.admin_urls`,
dins de l'espai de noms `administration` (sessió d'administració i TOTP). Cap ruta pública."""

from django.urls import path

from . import entry_views, views

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
        "tresoreria/conciliacio/<int:line_id>/casa/",
        views.match_view,
        name="treasury_match_line",
    ),
    path(
        "tresoreria/conciliacio/<int:line_id>/moviments/",
        views.match_movements_view,
        name="treasury_match_movements",
    ),
    path(
        "tresoreria/conciliacio/<int:line_id>/liquidacio/",
        views.settlement_line_view,
        name="treasury_confirm_settlement_line",
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
    path(
        "tresoreria/revisar/liquidacio/<int:settlement_id>/tanca/",
        views.settlement_review_close_view,
        name="treasury_settlement_review_close",
    ),
    path(
        "tresoreria/conciliacio/<int:line_id>/desfer-exclusio/",
        views.undo_exclusion_view,
        name="treasury_undo_exclusion",
    ),
    # Tercer tall de la T-M04-15: traspàs, arqueig, anul·lar i liquidacions.
    path("tresoreria/traspas/", entry_views.transfer_view, name="treasury_transfer"),
    path("tresoreria/arqueig/", entry_views.cash_count_view, name="treasury_cash_count"),
    path(
        "tresoreria/moviments/<int:movement_id>/anulla/",
        entry_views.reverse_view,
        name="treasury_reverse",
    ),
    path(
        "tresoreria/carrecs/<int:charge_id>/pagament-a-ma/",
        entry_views.manual_payment_view,
        name="treasury_manual_payment",
    ),
    path("tresoreria/liquidacions/", entry_views.settlements_view, name="treasury_settlements"),
    path(
        "tresoreria/liquidacions/<int:settlement_id>/confirma/",
        entry_views.settlement_confirm_view,
        name="treasury_settlement_confirm",
    ),
]
