from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path(
        "pagaments/notificacions/<str:provider_code>",
        views.provider_notification,
        name="provider_notification",
    ),
]
