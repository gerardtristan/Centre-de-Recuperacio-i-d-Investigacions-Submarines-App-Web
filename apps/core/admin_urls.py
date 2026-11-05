"""Rutes de la base comuna a l'àrea d'administració: s'inclouen a `apps.accounts.admin_urls`,
dins de l'espai de noms `administration` (sessió d'administració i TOTP)."""

from django.urls import path

from .views import audit

urlpatterns = [
    path("registre/", audit.audit_log_view, name="audit_log"),
]
