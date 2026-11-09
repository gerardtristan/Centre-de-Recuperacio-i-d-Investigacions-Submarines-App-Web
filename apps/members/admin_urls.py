"""Rutes del M01 a l'àrea d'administració: s'inclouen a `apps.accounts.admin_urls`, dins de
l'espai de noms `administration` (sessió d'administració i TOTP)."""

from django.urls import path

from .views import admin, admin_member_edit

urlpatterns = [
    path("importacions/cluber/", admin.cluber_preview_view, name="cluber_preview"),
    path("socis/altes/", admin.join_requests_view, name="join_requests"),
    path("socis/altes/nova/", admin.join_in_person_view, name="join_in_person"),
    path("socis/altes/<int:pk>/aprova/", admin.join_approve_view, name="join_approve"),
    path("socis/altes/<int:pk>/rebutja/", admin.join_reject_view, name="join_reject"),
    path("socis/", admin.members_list_view, name="members_list"),
    path("socis/exporta/", admin.members_export_view, name="members_export"),
    path("socis/<int:pk>/", admin.member_detail_view, name="member_detail"),
    path("quotes/", admin.fees_view, name="fees"),
    path("quotes/<int:pk>/impagat/", admin.fee_mark_unpaid_view, name="fee_mark_unpaid"),
    path("quotes/<int:pk>/desmarca/", admin.fee_unmark_unpaid_view, name="fee_unmark_unpaid"),
    path("socis/<int:pk>/edita/", admin_member_edit.member_edit_view, name="member_edit"),
    path(
        "socis/<int:pk>/data-alta/",
        admin_member_edit.member_join_date_view,
        name="member_join_date",
    ),
]
