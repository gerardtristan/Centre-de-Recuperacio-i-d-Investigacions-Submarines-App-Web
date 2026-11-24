"""Ajustos del 07 (T-M07-03; M07-6, «Valors configurables»). Per valor: fora de rang es rebutja,
el canvi queda al registre amb el valor anterior i sense permís és «no trobat». Els permisos
reals són del catàleg del nucli (T-M07-02): aquí l'apartat es declara només per a la prova, com
fa `core/tests/test_business_settings.py`. Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse

from apps.core import business_settings, permissions
from apps.core.models import AuditEntry, Role, RolePermission, Setting
from apps.core.permission_catalog import CATALOG, Permission
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client

pytestmark = pytest.mark.django_db
R = Role.Code
SECTION = business_settings.section_code("website")

# Clau: (valor inicial, valor vàlid, valors fora de rang o de tipus).
VALUES = {
    "website.home_activities_count": (6, 12, [0, 13, "6"]),
    "website.news_on_home": (3, 0, [-1, 11]),
    "website.newsletter_enabled": (False, True, ["sí", 1]),
    "website.newsletter_confirm_hours": (48, 168, [0, 169]),
    "website.contact_enabled": (False, True, ["sí", 1]),
    "website.contact_retention_months": (6, 24, [0, 25]),
    "website.club_contact": ("", "Carrer Inventat 1, Barcelona", ["x" * 501, 5]),
}


@pytest.fixture
def section(monkeypatch):
    """L'apartat «website» al catàleg, amb «Sí» per a l'administrador (el que farà T-M07-02)."""
    extra = Permission(
        code=SECTION, ref="TEST-W", description="Web", allowed_scopes=("all", "read")
    )
    monkeypatch.setattr(permissions, "CATALOG", {**CATALOG, SECTION: extra})
    RolePermission.objects.create(
        role=Role.objects.get(code=R.ADMINISTRATOR), permission_code=SECTION, scope="all"
    )


def test_the_section_has_its_values_with_the_switches_off():
    settings = Setting.objects.filter(module="website")
    assert {s.key: s.initial_value for s in settings} == {k: v[0] for k, v in VALUES.items()}
    assert not any(s.affects_money or s.effective_dated for s in settings)
    assert business_settings.get("website.newsletter_enabled") is False
    assert business_settings.get("website.contact_enabled") is False


@pytest.mark.parametrize("key", VALUES)
def test_out_of_range_is_rejected_and_nothing_is_saved(section, make_admin, key):  # noqa: F811
    account = make_admin(R.ADMINISTRATOR)
    for value in VALUES[key][2]:
        with pytest.raises(ValidationError):
            business_settings.change(key, value, account, "Prova")
    assert not Setting.objects.get(key=key).versions.exists()


@pytest.mark.parametrize("key", VALUES)
def test_a_valid_change_is_recorded_with_the_previous_value(section, make_admin, key):  # noqa: F811
    initial, valid, _wrong = VALUES[key]
    account = make_admin(R.ADMINISTRATOR)
    business_settings.change(key, valid, account, "Prova")
    assert business_settings.get(key) == valid
    entry = AuditEntry.objects.get(action=business_settings.ACTION_CHANGED, field=key)
    assert (entry.actor_account_id, entry.old_value, entry.new_value) == (
        account.pk, initial, valid,
    )  # fmt: skip


@pytest.mark.parametrize("key", VALUES)
def test_a_role_without_the_section_gets_not_found(section, make_admin, key):  # noqa: F811
    with pytest.raises(Http404):
        business_settings.change(key, VALUES[key][1], make_admin(R.SECRETARY), "Prova")
    assert business_settings.get(key) == VALUES[key][0]


@pytest.mark.parametrize("role", [R.ADMINISTRATOR, R.PRESIDENT, R.SECRETARY])
def test_until_t_m07_02_the_screen_is_not_found_for_everyone(make_admin, role):  # noqa: F811
    client = admin_client(make_admin(role))
    section = reverse("administration:settings_section", args=["website"])
    assert client.get(section).status_code == 404
    key = "website.newsletter_enabled"
    detail = reverse("administration:setting_detail", args=["website", key])
    assert client.post(detail, {"value": "on", "note": "Prova"}).status_code == 404
    assert business_settings.get("website.newsletter_enabled") is False
