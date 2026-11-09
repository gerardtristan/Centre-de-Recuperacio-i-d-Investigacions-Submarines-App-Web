"""Rutes del M01 a l'àrea d'administració: s'inclouen a `apps.accounts.admin_urls`, dins de
l'espai de noms `administration` (sessió d'administració i TOTP)."""

from django.urls import path

from .views import admin, admin_requests

urlpatterns = [
    path("importacions/cluber/", admin.cluber_preview_view, name="cluber_preview"),
    path("socis/altes/nova/", admin.join_in_person_view, name="join_in_person"),
    path("socis/", admin.members_list_view, name="members_list"),
    path("socis/exporta/", admin.members_export_view, name="members_export"),
    path("socis/<int:pk>/", admin.member_detail_view, name="member_detail"),
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
