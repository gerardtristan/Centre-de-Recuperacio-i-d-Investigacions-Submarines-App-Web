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
]
