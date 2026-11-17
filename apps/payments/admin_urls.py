"""Rutes del 05a a l'àrea d'administració: s'inclouen a `apps.accounts.admin_urls`, dins de
l'espai de noms `administration` (sessió d'administració i TOTP). Cap ruta pública."""

from django.urls import path

from . import admin_views, payment_admin_views, remittance_views

urlpatterns = [
    path("pagaments/", payment_admin_views.payments_view, name="payments_list"),  # T-M05b-16
    path("pagaments/mandats/", admin_views.mandates_view, name="payments_mandates"),
    path(
        "pagaments/mandats/<int:mandate_id>/revoca/",
        admin_views.mandate_revoke_view,
        name="payments_mandate_revoke",
    ),
    path("pagaments/campanya/", admin_views.campaign_view, name="payments_campaign"),
    # Remeses (T-M05b-09 i 10; B3).
    path("pagaments/remeses/", remittance_views.remittances_view, name="payments_remittances"),
    path(
        "pagaments/remeses/<int:remittance_id>/",
        remittance_views.remittance_view,
        name="payments_remittance",
    ),
    path(
        "pagaments/remeses/<int:remittance_id>/avisos/",
        remittance_views.remittance_notices_view,
        name="payments_remittance_notices",
    ),
    path(
        "pagaments/remeses/<int:remittance_id>/fitxer/",
        remittance_views.remittance_file_view,
        name="payments_remittance_file",
    ),
]
