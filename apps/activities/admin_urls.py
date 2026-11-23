"""Rutes del 02 a l'àrea d'administració: s'inclouen a `apps.accounts.admin_urls`, dins de l'espai
de noms `administration` (sessió d'administració i TOTP). Cada vista comprova el seu permís."""

from django.urls import path

from .views import admin_activities as activities
from .views import admin_catalogue as entries
from .views import admin_places as places

urlpatterns = [
    path("activitats/", activities.activities_view, name="activities"),
    path("activitats/curs/nou/", activities.activity_course_add_view, name="activity_course_add"),
    path(
        "activitats/sortida/nova/", activities.activity_outing_add_view, name="activity_outing_add"
    ),
    path("activitats/<int:pk>/", activities.activity_detail_view, name="activity_detail"),
    path("activitats/<int:pk>/edita/", activities.activity_edit_view, name="activity_edit"),
    path("activitats/llocs/", places.places_view, name="places"),
    path("activitats/llocs/nou/", places.place_add_view, name="place_add"),
    path("activitats/llocs/<int:pk>/", places.place_detail_view, name="place_detail"),
    path("activitats/cataleg/", entries.catalogue_view, name="catalogue"),
    path("activitats/cataleg/nova/", entries.entry_add_view, name="catalogue_entry_add"),
    path("activitats/cataleg/<int:pk>/", entries.entry_detail_view, name="catalogue_entry"),
]
