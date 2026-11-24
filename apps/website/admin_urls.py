"""Rutes d'administració del 07 (M07-8, `/gestio/web/`): s'inclouen a `apps.accounts.admin_urls`,
dins de l'espai de noms `administration`. Totes demanen sessió i permís."""

from django.urls import path

from . import admin_views as views

urlpatterns = [
    path("web/contacte/", views.inbox_view, name="website_contact"),
    path("web/contacte/<int:pk>/", views.message_view, name="website_contact_message"),
    path("web/contacte/<int:pk>/respon/", views.reply_view, name="website_contact_reply"),
    path("web/contacte/<int:pk>/tanca/", views.close_view, name="website_contact_close"),
    path("web/contacte/motius/", views.reasons_view, name="website_contact_reasons"),
    path("web/contacte/motius/nou/", views.reason_edit_view, name="website_contact_reason_add"),
    path(
        "web/contacte/motius/<int:pk>/",
        views.reason_edit_view,
        name="website_contact_reason_edit",
    ),
    path("web/butlleti/", views.newsletters_view, name="website_newsletters"),
    path("web/butlleti/nou/", views.newsletter_edit_view, name="website_newsletter_add"),
    path("web/butlleti/<int:pk>/", views.newsletter_edit_view, name="website_newsletter_edit"),
    path(
        "web/butlleti/<int:pk>/envia/", views.newsletter_send_view, name="website_newsletter_send"
    ),
]
