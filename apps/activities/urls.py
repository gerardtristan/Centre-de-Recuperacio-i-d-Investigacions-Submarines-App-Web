"""Rutes del 02 fora de l'administració. La inscripció d'un convidat és pública i declarada
(RN-40); la del soci és a l'àrea personal. Les d'administració són a `admin_urls.py`."""

from django.urls import path

from .views import guest_enrolment, member_enrolment

app_name = "activities"

urlpatterns = [
    path("activitats/<int:pk>/inscripcio/", guest_enrolment.guest_enrol_view, name="guest_enrol"),
    # Àrea personal (sessió obligatòria): la persona és la del compte (T-M02-11).
    path(
        "socis/activitats/<int:pk>/inscripcio/",
        member_enrolment.member_enrol_view,
        name="member_enrol",
    ),
]
