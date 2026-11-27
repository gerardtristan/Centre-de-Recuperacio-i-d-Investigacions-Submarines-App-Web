"""Rutes d'administració del 07 (M07-8, `/gestio/web/`): s'inclouen a `apps.accounts.admin_urls`,
dins de l'espai de noms `administration`. Totes demanen sessió i permís."""

from django.urls import path

from . import admin_views as views
from . import editor_views
from . import help_admin_views as help_views
from . import menu_admin_views as menu_views
from . import news_admin_views as news_views
from . import tutorial_admin_views as tutorial_views

urlpatterns = [
    # T-M07-06a (WP1): pàgines i editor de blocs.
    path("web/pagines/", editor_views.pages_view, name="website_pages"),
    path("web/pagines/<int:pk>/", editor_views.editor_view, name="website_page_editor"),
    path(
        "web/pagines/<int:pk>/accio/",
        editor_views.editor_action_view,
        name="website_page_editor_action",
    ),
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
    # T-M07-10b (WP4): tutorials.
    path("web/tutorials/", tutorial_views.admin_list_view, name="website_tutorials"),
    path("web/tutorials/nou/", tutorial_views.admin_edit_view, name="website_tutorial_add"),
    path("web/tutorials/<int:pk>/", tutorial_views.admin_edit_view, name="website_tutorial_edit"),
    path(
        "web/tutorials/<int:pk>/publica/",
        tutorial_views.admin_publish_view,
        name="website_tutorial_publish",
    ),
    # T-M07-21 (WP9): menú, capçalera i peu.
    path("web/menu/", menu_views.admin_menu_view, name="website_menu"),
    path("web/menu/nou/", menu_views.admin_item_view, name="website_menu_item_add"),
    path("web/menu/<int:pk>/", menu_views.admin_item_view, name="website_menu_item_edit"),
    path(
        "web/menu/<int:pk>/treu/",
        menu_views.admin_item_remove_view,
        name="website_menu_item_remove",
    ),
]
