"""Entrada d'administració, sota ADMIN_URL_PATH. Sense cap ruta de recuperació per correu."""

from django.urls import path

from . import views
from .security import AREA_ADMIN

app_name = "administration"

urlpatterns = [
    path("", views.admin_home, name="home"),
    path("entrar/", views.login_view, {"area": AREA_ADMIN}, name="login"),
    path("entrar/codi/", views.login_totp_view, {"area": AREA_ADMIN}, name="login_totp"),
    path("entrar/doble-factor/", views.totp_enrol_view, name="totp_enrol"),
    path("sortir/", views.logout_view, {"area": AREA_ADMIN}, name="logout"),
]
