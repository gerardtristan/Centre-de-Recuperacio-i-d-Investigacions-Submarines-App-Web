"""Rutes del 02 a l'àrea d'administració: s'inclouen a `apps.accounts.admin_urls`, dins de l'espai
de noms `administration` (sessió d'administració i TOTP). Cada vista comprova el seu permís."""

from django.urls import path

from .views import admin_activities as activities
from .views import admin_catalogue as entries
from .views import admin_certifications as certifications
from .views import admin_filings as filings
from .views import admin_places as places
from .views import (
    assessment,
    attendance,
    card_photos,
    environment,
    message,
    outcomes,
    reinforcement,
    reports,
)

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
    # T-M02-44b: homologacions a la federació (AC25 i AC26).
    path("homologacions/", filings.filings_view, name="filings"),
    path("homologacions/csv/", filings.filings_csv_view, name="filings_csv"),
    path("homologacions/demana/", filings.filing_request_view, name="filing_request"),
    # T-M02-52b (AC29): les titulacions d'una persona, des de la fitxa del soci.
    path(
        "titulacions/persona/<int:person_id>/",
        certifications.person_certifications_view,
        name="person_certifications",
    ),
    path("homologacions/<int:pk>/", filings.filing_detail_view, name="filing_detail"),
    path("homologacions/<int:pk>/tramitada/", filings.filing_filed_view, name="filing_filed"),
    path("homologacions/<int:pk>/feta/", filings.filing_done_view, name="filing_done"),
    path("homologacions/<int:pk>/rebutja/", filings.filing_reject_view, name="filing_reject"),
    # T-M02-42b: la foto del carnet en nom de la persona (AC25; només amb VC-56 encès).
    path(
        "homologacions/titulacions/<int:pk>/foto/",
        card_photos.admin_photo_view,
        name="certification_photo",
    ),
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
    # T-M02-19b: resultats del curs (AC12) i certificat (AC13)
    path("activitats/<int:pk>/resultats/", outcomes.outcomes_view, name="course_outcomes"),
    path(
        "activitats/<int:pk>/certificat/<int:enrolment_pk>/",
        outcomes.certificate_view,
        name="course_certificate",
    ),
    # T-M02-24b: informes operatius (AC20; l'instructor, només les seves activitats)
    path("activitats/informes/", reports.occupancy_view, name="activity_reports"),
    path(
        "activitats/<int:pk>/participants/",
        reports.participants_view,
        name="activity_participants",
    ),
    path("activitats/<int:pk>/horari/", reports.schedule_view, name="activity_schedule"),
    # T-M02-20b: resultats ambientals d'una sortida i fitxa de projecte (AC14)
    path(
        "activitats/<int:pk>/medi-ambient/",
        environment.results_view,
        name="activity_environment",
    ),
    path(
        "activitats/projectes/<int:pk>/",
        environment.project_view,
        name="environmental_project",
    ),
    # T-M02-18b: classes de reforç (proposta AC10b, decisió AC11)
    path("activitats/<int:pk>/reforc/", reinforcement.list_view, name="reinforcement_list"),
    path(
        "activitats/<int:pk>/reforc/proposa/<int:enrolment_pk>/",
        reinforcement.propose_view,
        name="reinforcement_propose",
    ),
    # T-M02-21c: missatge de l'organitzador als inscrits (AC15)
    path("activitats/<int:pk>/missatge/", message.message_view, name="activity_message"),
]
