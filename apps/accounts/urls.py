from django.urls import path

from . import views
from .security import AREA_PERSONAL

app_name = "accounts"

urlpatterns = [
    path("entrar/", views.login_view, {"area": AREA_PERSONAL}, name="login"),
    path("entrar/codi/", views.login_totp_view, {"area": AREA_PERSONAL}, name="login_totp"),
    path("sortir/", views.logout_view, {"area": AREA_PERSONAL}, name="logout"),
]
