"""Rutes del 02 a l'àrea d'administració: s'inclouen a `apps.accounts.admin_urls`, dins de l'espai
de noms `administration` (sessió d'administració i TOTP). Cada ruta declara el seu permís a
`apps/activities/permissions.py`."""

from django.urls import path

from .models import TrainingCatalogueEntry
from .views import admin_activities as activities
from .views import admin_catalogue as catalogue

COURSE = {"kind": TrainingCatalogueEntry.Kind.COURSE}
SPECIALITY = {"kind": TrainingCatalogueEntry.Kind.SPECIALITY}

urlpatterns = [
    # --- Catàlegs (T-M02-05) ---
    path("cataleg/cursos/", catalogue.catalogue_list_view, COURSE, name="catalogue_courses"),
    path(
        "cataleg/especialitats/",
        catalogue.catalogue_list_view,
        SPECIALITY,
        name="catalogue_specialities",
    ),
    path(
        "cataleg/cursos/nou/",
        catalogue.catalogue_entry_add_view,
        COURSE,
        name="catalogue_course_add",
    ),
    path(
        "cataleg/especialitats/nova/",
        catalogue.catalogue_entry_add_view,
        SPECIALITY,
        name="catalogue_speciality_add",
    ),
    path(
        "cataleg/fitxes/<int:pk>/", catalogue.catalogue_entry_edit_view, name="catalogue_entry_edit"
    ),
    path(
        "cataleg/fitxes/<int:pk>/preus/",
        catalogue.catalogue_entry_prices_view,
        name="catalogue_entry_prices",
    ),
    path(
        "cataleg/fitxes/<int:pk>/estat/",
        catalogue.catalogue_entry_active_view,
        name="catalogue_entry_active",
    ),
    path("sortides/tipus/", catalogue.outing_types_view, name="outing_types"),
    path(
        "sortides/tipus/<int:pk>/estat/",
        catalogue.outing_type_active_view,
        name="outing_type_active",
    ),
    path(
        "sortides/subtipus/<int:pk>/estat/",
        catalogue.outing_subtype_active_view,
        name="outing_subtype_active",
    ),
    path("projectes/", catalogue.projects_view, name="projects"),
    path("projectes/<int:pk>/", catalogue.project_detail_view, name="project_detail"),
    # --- Activitats (T-M02-06) ---
    path("activitats/", activities.activities_view, name="activities"),
    path("activitats/curs/nou/", activities.activity_course_add_view, name="activity_course_add"),
    path(
        "activitats/sortida/nova/", activities.activity_outing_add_view, name="activity_outing_add"
    ),
    path("activitats/<int:pk>/", activities.activity_detail_view, name="activity_detail"),
    path("activitats/<int:pk>/edita/", activities.activity_edit_view, name="activity_edit"),
    path("activitats/<int:pk>/pas/", activities.activity_step_view, name="activity_step"),
    path("activitats/<int:pk>/reobre/", activities.activity_reopen_view, name="activity_reopen"),
    path("activitats/<int:pk>/cancella/", activities.activity_cancel_view, name="activity_cancel"),
    path(
        "activitats/<int:pk>/programa/",
        activities.activity_programme_view,
        name="activity_programme",
    ),
    path("activitats/<int:pk>/sessions/nova/", activities.session_add_view, name="session_add"),
    path(
        "activitats/<int:pk>/sessions/<int:session_pk>/",
        activities.session_edit_view,
        name="session_edit",
    ),
    path(
        "activitats/<int:pk>/sessions/<int:session_pk>/cancella/",
        activities.session_cancel_view,
        name="session_cancel",
    ),
]
