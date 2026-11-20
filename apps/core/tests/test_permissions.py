"""Catàleg, configuració inicial i motor de permisos (059; RN-RP-01 a 05; CA-RP-01 a 03, 08,
09 i 13). Només dades inventades."""

from dataclasses import replace

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404, HttpResponse
from django.test import RequestFactory

from apps.core import permissions
from apps.core.models import AccountRole, PermissionMatrixVersion, Role, RolePermission
from apps.core.permission_catalog import (
    ADMINISTRATOR_ONLY,
    CATALOG,
    KNOWN_SCOPES,
    PERMISSIONS,
    SCOPE_OWN_SESSIONS,
    Permission,
    editable_initial_cells,
)
from apps.core.permissions import (
    effective_permissions,
    has_perm,
    permission_required,
    register_scope_check,
    request_permissions,
    require_perm,
    scope_for,
)

R = Role.Code
MANAGEMENT_ROLES = [code for code in R.values if code not in ("member", "visitor", "guest")]


# --- Catàleg -----------------------------------------------------------------------------


def test_codes_are_unique_and_prefixed_by_module():
    codes = [p.code for p in PERMISSIONS]
    assert len(codes) == len(set(codes))
    modules = {
        "core",
        "members",
        "treasury",
        "payments",
        "licences",
        "expenses",
        "grants",
        "settings",
    }
    assert {p.module for p in PERMISSIONS} <= modules
    refs = [p.ref for p in PERMISSIONS]
    assert len(refs) == len(set(refs))


@pytest.mark.parametrize("perm", PERMISSIONS, ids=lambda p: p.code)
def test_catalog_entry_is_coherent(perm):
    assert perm.allowed_scopes and set(perm.allowed_scopes) <= KNOWN_SCOPES
    assert perm.kind in {"action", "field"}
    assert set(perm.initial.values()) <= set(perm.allowed_scopes)
    assert set(perm.initial) <= set(MANAGEMENT_ROLES)
    assert all(req in CATALOG for req in perm.requires)
    # La configuració inicial respecta els requisits (RN-RP-03).
    for role in perm.initial:
        assert all(role in CATALOG[req].initial for req in perm.requires)
    if perm.protected:
        assert perm.protected_by


def test_user_and_role_management_is_protected_and_only_for_administrators():
    # 059, regla protegida 13.
    for code in ADMINISTRATOR_ONLY:
        assert CATALOG[code].protected
        assert dict(CATALOG[code].initial) == {R.ADMINISTRATOR: "all"}


def test_birth_date_and_locked_data_are_protected():
    assert CATALOG["members.field.birth_date"].protected
    assert CATALOG["core.locked_data.view"].protected


# --- Configuració inicial (T-RP-04) ------------------------------------------------------


@pytest.mark.django_db
def test_roles_are_loaded():
    assert Role.objects.count() == 14
    assert set(Role.objects.filter(is_management=True).values_list("code", flat=True)) == set(
        MANAGEMENT_ROLES
    )


@pytest.mark.django_db
def test_initial_matrix_in_the_database_matches_the_catalog():
    stored = sorted(RolePermission.objects.values_list("role__code", "permission_code", "scope"))
    assert stored == editable_initial_cells()
    assert not RolePermission.objects.filter(
        permission_code__in=[p.code for p in PERMISSIONS if p.protected]
    ).exists()
    assert PermissionMatrixVersion.objects.get(number=1).diff


CELLS = [(perm, role) for perm in PERMISSIONS for role in MANAGEMENT_ROLES]


@pytest.mark.parametrize(("perm", "role"), CELLS, ids=[f"{p.ref}-{p.code}-{r}" for p, r in CELLS])
def test_initial_matrix_cell(make_admin, perm, role):
    # CA-RP-13: cada cel·la de la matriu, amb el seu «sí» (i l'abast) o el seu «no».
    account = make_admin(role)
    assert scope_for(account, perm.code) == perm.initial.get(role)


@pytest.mark.django_db
def test_communications_shop_and_board_start_without_permissions(make_admin):
    for role in (R.COMMUNICATIONS_MANAGER, R.SHOP_MANAGER):
        assert effective_permissions(make_admin(role)) == {}
    # La Junta: «Cons.» de tipus i preus de les llicències (LC8) i, al 09, consulta del marge i
    # dels informes, els documents de justificació (protegits, 051) i els ajuts (T-M09-30).
    assert effective_permissions(make_admin(R.BOARD)) == {
        "licences.prices": "read",
        "expenses.margin.view": "read",
        "expenses.reports": "read",
        "expenses.documents.open": "all",
        "grants.view": "all",
        "grants.calls.manage": "all",
        "grants.eligibility": "all",
        "grants.applications.prepare": "own_applications",
        "grants.applications.resolve": "own_applications",
        "grants.applications.amendments": "own_applications",
        "grants.justification": "read",
        "grants.documents.open": "all",
    }


# --- Motor -------------------------------------------------------------------------------


@pytest.mark.django_db
class TestEngine:
    def test_union_takes_the_widest_scope(self, make_admin):
        # RN-RP-02: secretaria (tot) + tresorer (dades mínimes) → tot.
        assert scope_for(make_admin(R.TREASURER), "members.list") == "read_minimal"
        assert scope_for(make_admin(R.SECRETARY, R.TREASURER), "members.list") == "all"

    def test_union_adds_permissions_of_every_role(self, make_admin):
        account = make_admin(R.SECRETARY, R.TREASURER)
        assert has_perm(account, "members.unpaid.mark")  # del tresorer
        assert has_perm(account, "members.create_in_person")  # de la secretaria

    def test_read_only_scope_does_not_allow_writing(self, make_admin):
        treasurer = make_admin(R.TREASURER)
        assert has_perm(treasurer, "members.licence_record.manage")
        assert not has_perm(treasurer, "members.licence_record.manage", write=True)
        assert has_perm(make_admin(R.SECRETARY), "members.licence_record.manage", write=True)

    def test_superuser_flag_grants_nothing(self, make_admin):
        account = make_admin()
        account.is_superuser = True
        account.save()
        assert effective_permissions(account) == {}
        assert not has_perm(account, "core.accounts.manage")

    def test_personal_account_never_has_role_permissions(self, make_admin, personal_account):
        # El compte personal no hereta cap rol (059, punt 4.2), encara que algú n'hi posi un.
        AccountRole.objects.create(
            admin_account=personal_account, role=Role.objects.get(code=R.ADMINISTRATOR)
        )
        assert effective_permissions(personal_account) == {}

    def test_disabled_admin_has_no_permissions(self, make_admin):
        account = make_admin(R.ADMINISTRATOR)
        account.status = account.Status.DISABLED
        account.save()
        assert effective_permissions(account) == {}

    def test_anonymous_has_no_permissions(self):
        from django.contrib.auth.models import AnonymousUser

        assert effective_permissions(AnonymousUser()) == {}
        assert effective_permissions(None) == {}

    def test_removed_role_stops_counting_at_once(self, make_admin):
        # CA-RP-01: la petició següent ja no té cap permís de tresorer.
        account = make_admin(R.TREASURER, R.EQUIPMENT_MANAGER)
        assert has_perm(account, "members.unpaid.mark")
        AccountRole.objects.filter(admin_account=account, role__code=R.TREASURER).update(
            removed_at="2026-11-01T10:00:00Z"
        )
        assert not has_perm(account, "members.unpaid.mark")

    def test_removing_a_cell_affects_every_account_with_the_role(self, make_admin):
        # CA-RP-02
        first, second = make_admin(R.TREASURER), make_admin(R.TREASURER)
        RolePermission.objects.filter(
            role__code=R.TREASURER, permission_code="members.requests.approve_join"
        ).delete()
        assert not has_perm(first, "members.requests.approve_join")
        assert not has_perm(second, "members.requests.approve_join")

    def test_protected_permission_in_the_database_is_ignored(self, make_admin):
        # CA-RP-03 i CA-RP-09: una fila escrita directament no dona la regla protegida.
        president = make_admin(R.PRESIDENT)
        for code in ("core.accounts.manage", "members.field.birth_date"):
            RolePermission.objects.create(
                role=Role.objects.get(code=R.PRESIDENT), permission_code=code, scope="all"
            )
            assert not has_perm(president, code)

    def test_row_with_a_scope_not_allowed_is_ignored(self, make_admin):
        RolePermission.objects.create(
            role=Role.objects.get(code=R.INSTRUCTOR),
            permission_code="members.export",
            scope="own_sessions",
        )
        assert not has_perm(make_admin(R.INSTRUCTOR), "members.export")

    def test_unknown_permission_code_is_a_programming_error(self, make_admin):
        with pytest.raises(ImproperlyConfigured):
            has_perm(make_admin(R.ADMINISTRATOR), "members.no_existeix")


@pytest.mark.django_db
class TestObjectScope:
    """CA-RP-08: avaluar només a les sessions on fa classe, tingui el rol que tingui."""

    @pytest.fixture(autouse=True)
    def evaluate_permission(self, monkeypatch):
        perm = Permission(
            code="activities.evaluate",
            ref="TEST",
            description="Avaluar pràctiques",
            allowed_scopes=(SCOPE_OWN_SESSIONS,),
        )
        monkeypatch.setattr(permissions, "CATALOG", {**CATALOG, perm.code: perm})
        monkeypatch.setattr(permissions, "_SCOPE_CHECKS", {})
        RolePermission.objects.create(
            role=Role.objects.get(code=R.COURSES_MANAGER),
            permission_code=perm.code,
            scope=SCOPE_OWN_SESSIONS,
        )

    class Session:
        def __init__(self, *instructors):
            self.instructor_ids = {a.pk for a in instructors}

    def test_only_sessions_where_they_teach(self, make_admin):
        register_scope_check(SCOPE_OWN_SESSIONS, lambda acc, obj: acc.pk in obj.instructor_ids)
        manager, other = make_admin(R.COURSES_MANAGER), make_admin(R.INSTRUCTOR)
        assert has_perm(manager, "activities.evaluate", self.Session(manager))
        assert not has_perm(manager, "activities.evaluate", self.Session(other))

    def test_without_a_registered_check_no_object_passes(self, make_admin):
        manager = make_admin(R.COURSES_MANAGER)
        assert has_perm(manager, "activities.evaluate")  # el permís hi és
        assert not has_perm(manager, "activities.evaluate", self.Session(manager))

    def test_only_known_scopes_can_be_registered(self):
        with pytest.raises(ImproperlyConfigured):
            register_scope_check("everything", lambda acc, obj: True)


@pytest.mark.django_db
class TestRequestHelpers:
    def request(self, account):
        request = RequestFactory().get("/")
        request.user = account
        return request

    def test_require_perm_raises_not_found(self, make_admin):
        request = self.request(make_admin(R.PRESIDENT))
        with pytest.raises(Http404):
            require_perm(request, "core.accounts.manage")
        assert require_perm(request, "members.requests.view") == "all"

    def test_decorator(self, make_admin):
        @permission_required("members.export")
        def view(request):
            return HttpResponse("ok")

        assert view(self.request(make_admin(R.SECRETARY))).status_code == 200
        with pytest.raises(Http404):
            view(self.request(make_admin(R.TREASURER)))

    def test_decorator_rejects_unknown_codes_at_import(self):
        with pytest.raises(ImproperlyConfigured):
            permission_required("members.no_existeix")

    def test_permissions_are_computed_once_per_request(self, make_admin, django_assert_num_queries):
        request = self.request(make_admin(R.SECRETARY))
        request_permissions(request)
        with django_assert_num_queries(0):
            request_permissions(request)
            require_perm(request, "members.export")


def test_permission_dataclass_is_frozen():
    with pytest.raises(AttributeError):
        CATALOG["members.export"].protected = True  # type: ignore[misc]
    assert replace(CATALOG["members.export"], protected=True).protected
