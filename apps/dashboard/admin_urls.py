"""Rutes del 08 a l'àrea d'administració (M08-8): s'inclouen a `apps.accounts.admin_urls`, dins
de l'espai de noms `administration`. DB1 a totes."""

from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("dashboard/<slug:panel>/", views.dashboard_view, name="dashboard_panel"),
]
