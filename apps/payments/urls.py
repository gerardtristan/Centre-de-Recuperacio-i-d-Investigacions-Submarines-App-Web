from django.urls import path

from . import card_views, mandate_views, preference_views, views
from .models import PaymentAttempt

app_name = "payments"

urlpatterns = [
    path(
        "pagaments/notificacions/<str:provider_code>",
        views.provider_notification,
        name="provider_notification",
    ),
    # Compte personal (M05b-8, «Rutes»). Sessió obligatòria per defecte (RN-40).
    path("socis/pagaments/mandat/", mandate_views.mandate_view, name="mandate"),
    path("socis/pagaments/mandat/revoca/", mandate_views.revoke_view, name="mandate_revoke"),
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
        "socis/pagaments/<int:charge_id>/transferencia/",
        views.pay_view,
        {"method": PaymentAttempt.Method.TRANSFER},
        name="pay_transfer",
    ),
    path(
        "socis/pagaments/<int:attempt_id>/estat/",
        views.attempt_status_view,
        name="attempt_status",
    ),
    path("socis/pagaments/<int:attempt_id>/rebut/", views.receipt_view, name="receipt"),
    path("socis/pagaments/metode/", preference_views.fee_method_view, name="fee_method"),
    path("socis/pagaments/targeta/", card_views.saved_card_view, name="saved_card"),
    # Convidat (T-M05b-08): públiques declarades; la credencial és l'enllaç de la sessió. Sota
    # `pagaments/` perquè `convidat/<testimoni>/` (core) no prengui cap camí com a testimoni.
    path("pagaments/convidat/", views.guest_charge_view, name="guest_charge"),
    path(
        "pagaments/convidat/targeta/",
        views.guest_pay_view,
        {"method": PaymentAttempt.Method.CARD},
        name="guest_pay_card",
    ),
    path(
        "pagaments/convidat/bizum/",
        views.guest_pay_view,
        {"method": PaymentAttempt.Method.BIZUM},
        name="guest_pay_bizum",
    ),
    path(
        "pagaments/convidat/transferencia/",
        views.guest_pay_view,
        {"method": PaymentAttempt.Method.TRANSFER},
        name="guest_pay_transfer",
    ),
    path("pagaments/convidat/estat/", views.guest_status_view, name="guest_status"),
    path("pagaments/convidat/rebut/", views.guest_receipt_view, name="guest_receipt"),
    # Proveïdor fals (`providers.fake.PAY_PATH`): només hi respon amb el proveïdor fals.
    path("pagaments/prova/<str:order_id>/", views.fake_pay_view, name="fake_pay"),
]
