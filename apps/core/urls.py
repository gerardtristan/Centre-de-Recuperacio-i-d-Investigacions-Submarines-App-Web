from django.conf import settings
from django.urls import path

from . import views
from .views import guest, pwa

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("salut/", views.health, name="health"),
    # T-M01-39b: la cua de «He oblidat la contrasenya» i dels correus, per al monitor.
    path("salut/cua/", views.queue_health, name="queue_health"),
    path("fitxers/<uuid:file_id>/", views.private_file, name="private_file"),
    path("service-worker.js", pwa.service_worker, name="service_worker"),  # T-M01-21
    # Enllaços de convidat (T-M00-02): públiques declarades; l'enllaç és la credencial.
    path("convidat/", guest.guest_view, name="guest"),
    path("convidat/enllac-nou/", guest.guest_link_request_view, name="guest_link_request"),
    path("convidat/<str:token>/", guest.guest_link_view, name="guest_link"),
    # Ajuda per instal·lar-la a l'iPhone (041; 079, A-28; T-M01-45): pública, només text.
    path("ajuda/iphone/", pwa.install_help_iphone, name="install_help_iphone"),
]

# Emmagatzematge local que imita Scaleway: només fora de producció (decisió 010).
if settings.PRIVATE_FILES_LOCAL_ALLOWED:
    urlpatterns.append(
        path("fitxers/local/<str:token>/", views.local_private_file, name="local_private_file")
    )
