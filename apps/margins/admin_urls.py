"""Rutes del 09 (marge d'una activitat) a l'àrea d'administració (M09-8): s'inclouran a
`apps.accounts.admin_urls`, dins de l'espai de noms `administration` (torn del nucli)."""

from django.urls import path

from . import views

urlpatterns = [
    path("marges/<int:activity_id>/", views.activity_view, name="activity_margin"),
    path("marges/<int:activity_id>/previst/", views.planned_view, name="activity_margin_planned"),
    path("marges/<int:activity_id>/tanca/", views.close_view, name="activity_margin_close"),
]
