"""Entrada d'administració, sota ADMIN_URL_PATH. Sense cap ruta de recuperació per correu."""

from django.urls import include, path

from . import views
from .security import AREA_ADMIN

app_name = "administration"

urlpatterns = [
    path("", views.admin_home, name="home"),
    path("comptes/", views.admin_accounts_view, name="accounts"),
    path(
        "comptes/<int:pk>/restablir/",
        views.reset_credentials_view,
        name="reset_credentials",
    ),
    path("entrar/", views.login_view, {"area": AREA_ADMIN}, name="login"),
    path("entrar/codi/", views.login_totp_view, {"area": AREA_ADMIN}, name="login_totp"),
    path("entrar/doble-factor/", views.totp_enrol_view, name="totp_enrol"),
    path(
        "entrar/contrasenya-nova/",
        views.temporary_password_change_view,
        name="change_temporary_credential",
    ),
    path("sortir/", views.logout_view, {"area": AREA_ADMIN}, name="logout"),
    # Rutes d'administració de la 00, del M01, de la 04 i del 05a, dins d'aquest espai de noms.
    path("", include("apps.core.admin_urls")),
    path("", include("apps.members.admin_urls")),
    path("", include("apps.treasury.admin_urls")),
    path("", include("apps.payments.admin_urls")),
    path("", include("apps.licences.admin_urls")),
    path("", include("apps.activities.admin_urls")),  # 02: activitats (T-M02-06)
    path("", include("apps.expenses.admin_urls")),  # 09: despeses (T-M09-06 i T-M09-15)
    path("", include("apps.margins.admin_urls")),  # 09: marge d'una activitat
    path("", include("apps.grants.admin_urls")),  # 09: ajuts (T-M09A-05)
    path("", include("apps.equipment.admin_urls")),  # 03: informes i cost d'ús (T-M03-19 i 22)
    path("", include("apps.website.admin_urls")),  # 07: safata i motius de contacte (WP5, WP8)
    path("", include("apps.dashboard.admin_urls")),  # 08: dashboard (T-M08-09)
    # Les pantalles «En construcció» també aquí (T-DX-50): a producció només les veu un compte
    # d'administrador amb el permís DX1 (P-90), i a /en-construccio/ seria a la zona de socis (401).
    path("en-construccio/", include("apps.previews.urls")),
]
