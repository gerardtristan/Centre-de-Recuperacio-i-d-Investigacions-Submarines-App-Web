"""Rutes dels ajuts a l'àrea d'administració: s'inclouen a `apps.accounts.admin_urls`, dins de
l'espai de noms `administration`."""

from django.urls import path

from . import views

urlpatterns = [
    path("ajuts/calendari/", views.calendar_view, name="grants_calendar"),
    path("ajuts/<int:pk>/justificacio/", views.justification_view, name="grant_justification"),
]
