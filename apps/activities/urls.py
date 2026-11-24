"""Rutes del 02 fora de l'administració. El llistat, el detall i la inscripció d'un convidat són
públics i declarats (RN-40); la inscripció del soci és a l'àrea personal. Les d'administració
són a `admin_urls.py`."""

from django.urls import path

from .views import (
    card_photos,
    guest_enrolment,
    member_certifications,
    member_enrolment,
    my_activities,
    public_pages,
)

app_name = "activities"

urlpatterns = [
    # Públiques declarades (RN-40; T-M02-08b): només dades de `public.py`.
    path("activitats/", public_pages.public_list_view, name="public_list"),
    path("activitats/<int:pk>/", public_pages.public_detail_view, name="public_detail"),
    path("activitats/<int:pk>/inscripcio/", guest_enrolment.guest_enrol_view, name="guest_enrol"),
    # Àrea personal (sessió obligatòria): la persona és la del compte (T-M02-11).
    path(
        "socis/activitats/<int:pk>/inscripcio/",
        member_enrolment.member_enrol_view,
        name="member_enrol",
    ),
    # «Les meves activitats» i el calendari d'una inscripció seva (T-M02-22b).
    path("socis/activitats/", my_activities.my_activities_view, name="mine"),
    path(
        "socis/activitats/inscripcions/<int:pk>/calendari.ics",
        my_activities.enrolment_calendar_view,
        name="enrolment_calendar",
    ),
    # T-M02-22c: el certificat emès d'una inscripció seva, per imprimir o desar com a PDF.
    path(
        "socis/activitats/inscripcions/<int:pk>/certificat/",
        my_activities.enrolment_certificate_view,
        name="enrolment_certificate",
    ),
    # T-M02-17b: «El meu progrés» d'una inscripció seva a un curs (HU-M02-14).
    path(
        "socis/activitats/inscripcions/<int:pk>/progres/",
        my_activities.enrolment_progress_view,
        name="enrolment_progress",
    ),
    # T-M02-44c: les titulacions de la persona i demanar l'homologació (RN-M02-50).
    path(
        "socis/titulacions/",
        member_certifications.my_certifications_view,
        name="my_certifications",
    ),
    # T-M02-42b: el titular puja la foto del carnet (RN-M02-47; només amb VC-56 encès).
    path(
        "socis/titulacions/<int:pk>/foto/",
        card_photos.my_photo_view,
        name="my_certification_photo",
    ),
]
