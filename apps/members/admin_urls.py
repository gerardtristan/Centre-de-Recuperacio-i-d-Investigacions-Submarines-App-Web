"""Rutes del M01 a l'àrea d'administració: s'inclouen a `apps.accounts.admin_urls`, dins de
l'espai de noms `administration` (sessió d'administració i TOTP)."""

from django.urls import path

from .views import admin, admin_licences, admin_member_edit, admin_requests

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
    # 079 (RN-M01-87): tornar a enviar la invitació del compte personal (M2 i P4).
    path(
        "socis/<int:pk>/invitacio/",
        admin_member_edit.member_invite_view,
        name="member_invite",
    ),
    path(
        "socis/<int:pk>/llicencies/nova/",
        admin_licences.licence_add_view,
        name="licence_add",
    ),
    path(
        "socis/<int:pk>/llicencies/<int:record_pk>/",
        admin_licences.licence_edit_view,
        name="licence_edit",
    ),
    # T-M01-17: canvis de tipus i baixes (P3a per consultar, P7 per resoldre).
    path("socis/sollicituds/", admin_requests.requests_list_view, name="member_requests"),
    path(
        "socis/sollicituds/<int:pk>/",
        admin_requests.request_detail_view,
        name="member_request_detail",
    ),
    path(
        "socis/<int:pk>/baixa/nova/", admin_requests.leave_create_view, name="member_leave_create"
    ),
]
urlpatterns += [
    path(
        "llicencies/pendents/",
        admin_licences.licence_bulk_confirm_view,
        name="licence_bulk_confirm",
    ),
]
