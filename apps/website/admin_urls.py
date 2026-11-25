"""Rutes d'administració del 07 (M07-8, `/gestio/web/`): s'inclouen a `apps.accounts.admin_urls`,
dins de l'espai de noms `administration`. Totes demanen sessió i permís."""

from django.urls import path

from . import admin_views as views
from . import help_admin_views as help_views
from . import news_admin_views as news_views

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
    # T-M07-08 (WP2): notícies.
    path("web/noticies/", news_views.admin_list_view, name="website_news"),
    path("web/noticies/nova/", news_views.admin_edit_view, name="website_news_add"),
    path("web/noticies/<int:pk>/", news_views.admin_edit_view, name="website_news_edit"),
    path(
        "web/noticies/<int:pk>/publica/", news_views.admin_publish_view, name="website_news_publish"
    ),
    path("web/noticies/<int:pk>/retira/", news_views.admin_retire_view, name="website_news_retire"),
    # T-M07-09b (WP4): preguntes freqüents.
    path("web/ajuda/", help_views.admin_list_view, name="website_help"),
    path("web/ajuda/temes/nou/", help_views.admin_topic_add_view, name="website_help_topic_add"),
    path("web/ajuda/nova/", help_views.admin_edit_view, name="website_help_add"),
    path("web/ajuda/<int:pk>/", help_views.admin_edit_view, name="website_help_edit"),
    path("web/ajuda/<int:pk>/publica/", help_views.admin_publish_view, name="website_help_publish"),
]
