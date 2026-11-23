from django.conf import settings
from django.urls import include, path

urlpatterns = [
    path(f"{settings.ADMIN_URL_PATH}/", include("apps.accounts.admin_urls")),
    path("", include("apps.accounts.urls")),
    path("", include("apps.core.urls")),
    path("", include("apps.members.urls")),
    path("", include("apps.payments.urls")),
    path("", include("apps.invoicing.urls")),  # 09: «Les meves factures» (T-M09-21)
    path("", include("apps.licences.urls")),
    path("", include("apps.activities.urls")),  # 02: inscripció de convidat (T-M02-14)
    path("en-construccio/", include("apps.previews.urls")),
]
