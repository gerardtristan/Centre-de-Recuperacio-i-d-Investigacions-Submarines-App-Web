from django.urls import path

from . import views
from .models import PaymentAttempt

app_name = "payments"

urlpatterns = [
    path(
        "pagaments/notificacions/<str:provider_code>",
        views.provider_notification,
        name="provider_notification",
    ),
    # Compte personal (M05b-8, «Rutes»). Sessió obligatòria per defecte (RN-40).
    path("socis/pagaments/<int:charge_id>/", views.charge_view, name="charge"),
    path(
        "socis/pagaments/<int:charge_id>/targeta/",
        views.pay_view,
        {"method": PaymentAttempt.Method.CARD},
        name="pay_card",
    ),
    path(
        "socis/pagaments/<int:charge_id>/bizum/",
        views.pay_view,
        {"method": PaymentAttempt.Method.BIZUM},
        name="pay_bizum",
    ),
    path(
        "socis/pagaments/<int:attempt_id>/estat/",
        views.attempt_status_view,
        name="attempt_status",
    ),
    path("socis/pagaments/<int:attempt_id>/rebut/", views.receipt_view, name="receipt"),
    # Proveïdor fals (`providers.fake.PAY_PATH`): només hi respon amb el proveïdor fals.
    path("pagaments/prova/<str:order_id>/", views.fake_pay_view, name="fake_pay"),
]
