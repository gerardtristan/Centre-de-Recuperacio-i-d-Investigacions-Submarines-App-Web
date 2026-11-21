"""Rutes del 02 a l'àrea d'administració: s'inclouen a `apps.accounts.admin_urls`, dins de l'espai
de noms `administration` (sessió d'administració i TOTP). Cada vista comprova el seu permís."""

from django.urls import path

from .views import admin_activities as activities

urlpatterns = [
    path("activitats/", activities.activities_view, name="activities"),
    path("activitats/<int:pk>/", activities.activity_detail_view, name="activity_detail"),
]
