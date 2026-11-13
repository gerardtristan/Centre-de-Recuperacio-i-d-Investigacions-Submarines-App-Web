from django.conf import settings
from django.urls import include, path

urlpatterns = [
    path(f"{settings.ADMIN_URL_PATH}/", include("apps.accounts.admin_urls")),
    path("", include("apps.accounts.urls")),
    path("", include("apps.core.urls")),
    path("", include("apps.members.urls")),
    path("", include("apps.payments.urls")),
]
