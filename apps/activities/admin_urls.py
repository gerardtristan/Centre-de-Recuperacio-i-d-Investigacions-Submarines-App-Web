"""Rutes del 02 a l'àrea d'administració: s'inclouen a `apps.accounts.admin_urls`, dins de l'espai
de noms `administration` (sessió d'administració i TOTP). Cada vista comprova el seu permís."""

from django.urls import path

from .views import admin_activities as activities
from .views import assessment, attendance

urlpatterns = [
    path("activitats/", activities.activities_view, name="activities"),
    path("activitats/curs/nou/", activities.activity_course_add_view, name="activity_course_add"),
    path(
        "activitats/sortida/nova/", activities.activity_outing_add_view, name="activity_outing_add"
    ),
    path("activitats/<int:pk>/", activities.activity_detail_view, name="activity_detail"),
    path("activitats/<int:pk>/edita/", activities.activity_edit_view, name="activity_edit"),
    # T-M02-16b: passar llista des del mòbil i incidències (AC9 per objecte)
    path("activitats/llista/", attendance.sessions_view, name="attendance_sessions"),
    path("activitats/<int:pk>/llista/", attendance.roll_view, name="attendance_roll"),
    path(
        "activitats/<int:pk>/llista/<int:session_pk>/",
        attendance.roll_view,
        name="attendance_roll_session",
    ),
    # T-M02-17b: full d'avaluació d'una pràctica (AC10a, només qui hi fa classe)
    path(
        "activitats/<int:pk>/avaluacio/<int:session_pk>/",
        assessment.sheet_view,
        name="assessment_sheet",
    ),
]
