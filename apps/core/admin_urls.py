"""Rutes de la base comuna a l'àrea d'administració: s'inclouen a `apps.accounts.admin_urls`,
dins de l'espai de noms `administration` (sessió d'administració i TOTP)."""

from django.urls import path

from .views import audit, bank_statement, business_settings, gdpr, guest, locked_data

urlpatterns = [
    path("registre/", audit.audit_log_view, name="audit_log"),
    # T-M01-22 (P-M01-F, pas 4): sol·licituds d'esborrat RGPD, amb M11.
    path("rgpd/", gdpr.gdpr_requests_view, name="gdpr_requests"),
    path("rgpd/<int:pk>/", gdpr.gdpr_request_detail_view, name="gdpr_request_detail"),
    # T-M00-04: consulta de dades bloquejades, amb M13 (protegit) i motiu.
    path("dades-bloquejades/", locked_data.locked_data_list_view, name="locked_data"),
    path(
        "dades-bloquejades/<int:pk>/",
        locked_data.locked_data_detail_view,
        name="locked_data_detail",
    ),
    # Enllaços de convidat (T-M00-02): M5 per a totes tres.
    path("enllacos-convidat/", guest.guest_links_admin_view, name="guest_links"),
    path("enllacos-convidat/<int:pk>/envia/", guest.guest_link_send_view, name="guest_link_send"),
    path(
        "enllacos-convidat/<int:pk>/revoca/",
        guest.guest_link_revoke_view,
        name="guest_link_revoke",
    ),
    # T-M00-01: importació de l'extracte bancari, amb M9 per a totes tres.
    path("importacions/extracte/", bank_statement.bank_statement_view, name="bank_statement"),
    path(
        "importacions/extracte/confirma/",
        bank_statement.bank_statement_confirm_view,
        name="bank_statement_confirm",
    ),
    path(
        "importacions/extracte/<int:pk>/desfes/",
        bank_statement.bank_statement_undo_view,
        name="bank_statement_undo",
    ),
    # T-AJ-02: ajustos de cada apartat, amb `settings.section.<apartat>` (RN-RP-22).
    path("ajustos/", business_settings.settings_index_view, name="settings"),
    path(
        "ajustos/<slug:section>/",
        business_settings.settings_section_view,
        name="settings_section",
    ),
    path(
        "ajustos/<slug:section>/<str:key>/",
        business_settings.setting_detail_view,
        name="setting_detail",
    ),
]
