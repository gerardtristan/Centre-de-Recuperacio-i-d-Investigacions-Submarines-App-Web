"""Rutes del 02 fora de l'administració. El llistat, el detall i la inscripció d'un convidat són
públics i declarats (RN-40); la inscripció del soci és a l'àrea personal. Les d'administració
són a `admin_urls.py`."""

from django.urls import path

from .views import guest_enrolment, member_enrolment, public_pages

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
]
