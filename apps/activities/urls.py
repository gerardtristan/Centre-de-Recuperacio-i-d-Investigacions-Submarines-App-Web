"""Rutes del 02 fora de l'administració. La inscripció d'un convidat és pública i declarada
(RN-40). Les d'administració són a `admin_urls.py`."""

from django.urls import path

from .views import guest_enrolment

app_name = "activities"

urlpatterns = [
    path("activitats/<int:pk>/inscripcio/", guest_enrolment.guest_enrol_view, name="guest_enrol"),
]
