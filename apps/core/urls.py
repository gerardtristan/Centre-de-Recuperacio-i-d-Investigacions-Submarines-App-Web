from django.conf import settings
from django.urls import path

from . import views
from .views import guest, pwa

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("salut/", views.health, name="health"),
    path("fitxers/<uuid:file_id>/", views.private_file, name="private_file"),
    path("service-worker.js", pwa.service_worker, name="service_worker"),  # T-M01-21
    # Enllaços de convidat (T-M00-02): públiques declarades; l'enllaç és la credencial.
    path("convidat/", guest.guest_view, name="guest"),
    path("convidat/enllac-nou/", guest.guest_link_request_view, name="guest_link_request"),
    path("convidat/<str:token>/", guest.guest_link_view, name="guest_link"),
]

# Emmagatzematge local que imita Scaleway: només fora de producció (decisió 010).
if settings.PRIVATE_FILES_LOCAL_ALLOWED:
    urlpatterns.append(
        path("fitxers/local/<str:token>/", views.local_private_file, name="local_private_file")
    )
