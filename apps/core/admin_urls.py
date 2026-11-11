"""Rutes de la base comuna a l'àrea d'administració: s'inclouen a `apps.accounts.admin_urls`,
dins de l'espai de noms `administration` (sessió d'administració i TOTP)."""

from django.urls import path

from .views import audit, gdpr, guest

urlpatterns = [
    path("registre/", audit.audit_log_view, name="audit_log"),
    # T-M01-22 (P-M01-F, pas 4): sol·licituds d'esborrat RGPD, amb M11.
    path("rgpd/", gdpr.gdpr_requests_view, name="gdpr_requests"),
    path("rgpd/<int:pk>/", gdpr.gdpr_request_detail_view, name="gdpr_request_detail"),
    # Enllaços de convidat (T-M00-02): M5 per a totes tres.
    path("enllacos-convidat/", guest.guest_links_admin_view, name="guest_links"),
    path("enllacos-convidat/<int:pk>/envia/", guest.guest_link_send_view, name="guest_link_send"),
    path(
        "enllacos-convidat/<int:pk>/revoca/",
        guest.guest_link_revoke_view,
        name="guest_link_revoke",
    ),
]
