"""Permisos del 07 i del 08 per cel·la i les pantalles dels seus ajustos (T-M07-02; CA-M07-18;
CA-M08-12; T-M08-02 i 03). La taula és la matriu inicial de M07-4 i M08-4 (planning.md), copiada a
mà: si el catàleg se n'aparta, la prova falla. Només dades inventades."""

import pytest
from django.urls import reverse

from apps.core import business_settings
from apps.core.models import Role
from apps.core.permissions import scope_for
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client

pytestmark = pytest.mark.django_db
R = Role.Code
Y, CONS, N = "all", "read", None
ROLES = (R.INSTRUCTOR, R.SECRETARY, R.COURSES_MANAGER, R.EQUIPMENT_MANAGER, R.TREASURER,
         R.HISTORY_DEPARTMENT, R.ADMINISTRATOR, R.PRESIDENT, R.BOARD)  # fmt: skip
# Instr., Secr., RCS, RM, Tres., DH, Admin., Pres., Junta.
WP1 = (N, N, N, N, N, N, Y, Y, N)
ADMIN = (N, N, N, N, N, N, Y, N, N)
MATRIX = {
    "website.pages": WP1,
    "website.news": WP1,  # WP2
    "website.media": WP1,  # WP3
    "website.help": (N, N, N, N, N, N, Y, Y, Y),  # WP4
    "website.contact": (N, Y, N, N, N, N, Y, N, N),  # WP5
    "website.newsletter": WP1,  # WP6
    "website.subscribers": ADMIN,  # WP7
    "website.contact_reasons": ADMIN,  # WP8
    "settings.section.website": (N, N, N, N, N, N, CONS, CONS, N),
    "settings.edit.website.home_activities_count": WP1,
    "settings.edit.website.news_on_home": WP1,
    "settings.edit.website.club_contact": WP1,
    "settings.edit.website.newsletter_enabled": ADMIN,
    "settings.edit.website.newsletter_confirm_hours": ADMIN,
    "settings.edit.website.contact_enabled": ADMIN,
    "settings.edit.website.contact_retention_months": ADMIN,
    "dashboard.view": (N, Y, Y, Y, Y, Y, Y, Y, N),  # DB1
    "dashboard.actions": (N, N, Y, N, Y, N, Y, Y, N),  # DB2
    "settings.section.dashboard": ADMIN,
    "settings.edit.dashboard.help_text": ADMIN,
    "settings.edit.dashboard.min_group_size": ADMIN,
}
CELLS = [(code, role, row[i]) for code, row in MATRIX.items() for i, role in enumerate(ROLES)]


@pytest.mark.parametrize(("code", "role", "expected"), CELLS, ids=[f"{c}-{r}" for c, r, _ in CELLS])
def test_cell(make_admin, code, role, expected):  # noqa: F811
    assert scope_for(make_admin(role), code) == expected


@pytest.mark.parametrize("role", [R.COMMUNICATIONS_MANAGER, R.SHOP_MANAGER])
def test_communications_and_shop_start_without_anything(make_admin, role):  # noqa: F811
    # El Responsable de comunicació, fins que la junta respongui la P-43 (M07-4).
    account = make_admin(role)
    assert not [code for code in MATRIX if scope_for(account, code)]


def section_url(section):
    return reverse("administration:settings_section", args=[section])


def detail_url(section, key):
    return reverse("administration:setting_detail", args=[section, key])


# --- Ajustos de la web (T-M07-03) ------------------------------------------------------------


def test_the_president_edits_the_home_page_values_but_not_the_switches(make_admin):  # noqa: F811
    client = admin_client(make_admin(R.PRESIDENT))
    assert client.get(section_url("website")).status_code == 200
    response = client.post(
        detail_url("website", "website.news_on_home"), {"value": "5", "note": "Prova"}
    )
    assert response.status_code == 302 and business_settings.get("website.news_on_home") == 5
    key = "website.newsletter_enabled"
    assert (
        client.post(detail_url("website", key), {"value": "1", "note": "Prova"}).status_code == 404
    )
    assert business_settings.get(key) is False


def test_the_administrator_turns_on_a_switch_and_it_is_recorded(make_admin):  # noqa: F811
    client = admin_client(make_admin(R.ADMINISTRATOR))
    key = "website.contact_enabled"
    response = client.post(detail_url("website", key), {"value": "1", "note": "Prova"})
    assert response.status_code == 302 and business_settings.get(key) is True


@pytest.mark.parametrize("role", [R.SECRETARY, R.TREASURER, R.BOARD])
def test_without_the_website_section_the_screen_is_not_found(make_admin, role):  # noqa: F811
    client = admin_client(make_admin(role))
    assert client.get(section_url("website")).status_code == 404
    key = "website.club_contact"
    assert (
        client.post(detail_url("website", key), {"value": "x", "note": "Prova"}).status_code == 404
    )
    assert business_settings.get(key) == ""


# --- Ajustos del dashboard (P-488 i P-487) ---------------------------------------------------


def test_the_administrator_sees_each_help_text_by_indicator_name_and_edits_it(make_admin):  # noqa: F811
    client = admin_client(make_admin(R.ADMINISTRATOR))
    page = client.get(section_url("dashboard")).content.decode()
    assert "Text d&#x27;ajuda d&#x27;un indicador: Socis actius" in page
    key = "dashboard.help_text.active_members"
    text = "Inclou els socis d'honor (inventat)."
    response = client.post(detail_url("dashboard", key), {"value": text, "note": "Prova"})
    assert response.status_code == 302 and business_settings.get(key) == text


@pytest.mark.parametrize("role", [R.PRESIDENT, R.TREASURER, R.SECRETARY])
def test_without_the_dashboard_section_the_screen_is_not_found(make_admin, role):  # noqa: F811
    client = admin_client(make_admin(role))
    assert client.get(section_url("dashboard")).status_code == 404
    key = "dashboard.help_text.retention"
    assert (
        client.post(detail_url("dashboard", key), {"value": "x", "note": "Prova"}).status_code
        == 404
    )
    assert business_settings.get(key) == ""
