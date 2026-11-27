from django.urls import path

from . import email_login_views, signup_views, views
from .security import AREA_PERSONAL

app_name = "accounts"

# Les rutes fixes van abans de les que porten un testimoni: «oblidada» o «reenviar» no s'han
# de llegir mai com un testimoni.
urlpatterns = [
    path("entrar/", views.login_view, {"area": AREA_PERSONAL}, name="login"),
    path("entrar/codi/", views.login_totp_view, {"area": AREA_PERSONAL}, name="login_totp"),
    # T-M01-56 (108, D.3): entrar amb un enllaç pel correu (apagat: «no trobat»).
    path("entrar/correu/", email_login_views.email_login_request_view, name="email_login_request"),
    path("entrar/correu/enllac/", email_login_views.email_login_view, name="email_login"),
    path(
        "entrar/correu/<str:token>/",
        email_login_views.email_login_link_view,
        name="email_login_link",
    ),
    path("sortir/", views.logout_view, {"area": AREA_PERSONAL}, name="logout"),
    # T-M01-53 (108, D): crear el compte personal en una sola pantalla.
    path("compte/nou/", signup_views.signup_view, name="signup"),
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
    path("compte/verificar/", views.verify_email_view, name="verify_email"),
    path(
        "compte/verificar/reenviar/",
        views.resend_verification_view,
        name="resend_verification",
    ),
    path("compte/verificar/<str:token>/", views.verify_email_link_view, name="verify_email_link"),
    # Canvi del correu d'entrada des del perfil (RN-M01-79): confirmació des de l'adreça nova.
    path("compte/correu/", views.change_email_view, name="change_email"),
    path("compte/correu/<str:token>/", views.change_email_link_view, name="change_email_link"),
    # Invitació per crear el compte personal en aprovar una alta (079, RN-M01-87).
    path("compte/invitacio/", views.invitation_view, name="invitation"),
    path("compte/invitacio/<str:token>/", views.invitation_link_view, name="invitation_link"),
    path("compte/contrasenya/", views.password_reset_view, name="password_reset"),
    path(
        "compte/contrasenya/oblidada/",
        views.password_reset_request_view,
        name="password_reset_request",
    ),
    path(
        "compte/contrasenya/<str:token>/",
        views.password_reset_link_view,
        name="password_reset_link",
    ),
]
