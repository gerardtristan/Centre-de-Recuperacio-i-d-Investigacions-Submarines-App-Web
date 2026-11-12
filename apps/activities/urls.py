"""Rutes públiques del 02 (T-M02-08). Les d'administració són a `admin_urls.py`."""

from django.urls import path

from .views import public

app_name = "activities"

urlpatterns = [
    path("activitats/", public.activities_view, name="list"),
    path("activitats/<int:pk>/", public.activity_view, name="detail"),
]
