from django.urls import path

from . import views
from .security import AREA_PERSONAL

app_name = "accounts"

urlpatterns = [
    path("entrar/", views.login_view, {"area": AREA_PERSONAL}, name="login"),
    path("entrar/codi/", views.login_totp_view, {"area": AREA_PERSONAL}, name="login_totp"),
    path("sortir/", views.logout_view, {"area": AREA_PERSONAL}, name="logout"),
    path("compte/verificar/", views.verify_email_view, name="verify_email"),
    path("compte/verificar/<str:token>/", views.verify_email_link_view, name="verify_email_link"),
    path("compte/seguretat/", views.security_view, name="security"),
    path(
        "compte/seguretat/doble-factor/",
        views.personal_totp_enrol_view,
        name="totp_enrol",
    ),
    path(
        "compte/seguretat/doble-factor/desactivar/",
        views.personal_totp_disable_view,
        name="totp_disable",
    ),
    path("compte/contrasenya/", views.password_reset_view, name="password_reset"),
    path(
        "compte/contrasenya/<str:token>/",
        views.password_reset_link_view,
        name="password_reset_link",
    ),
]
