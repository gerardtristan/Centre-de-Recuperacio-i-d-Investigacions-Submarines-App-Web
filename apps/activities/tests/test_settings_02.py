"""Apartat «Activitats» de la pantalla comuna d'ajustos (T-M02-28; M02-6, «Valors configurables»;
RN-RP-22). Cada rol veu l'apartat i només pot editar els seus valors; sense l'apartat, «no
trobat». Només dades inventades."""

import pytest
from django.urls import reverse

from apps.core import business_settings
from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client

pytestmark = pytest.mark.django_db
R = Role.Code
SECTION = reverse("administration:settings_section", args=["activities"])
OFFER = "activities.offer_accept_hours"  # VC-22


def editable(role, make_admin):  # noqa: F811
    rows = admin_client(make_admin(role)).get(SECTION).context["rows"]
    return {row["setting"].key for row in rows if row["editable"]}


def test_each_role_edits_only_its_values(make_admin):  # noqa: F811
    assert {
        "activities.default_payment_window_hours",
        "activities.homologation_target_agency",
    } <= editable(R.TREASURER, make_admin)
    manager = editable(R.COURSES_MANAGER, make_admin)
    assert {OFFER, "activities.default_requirements_mode"} <= manager
    assert "activities.default_payment_window_hours" not in manager
    # VC-25: el veu l'administrador; l'edició arriba amb el permís del nucli (T-M02-28b).
    rows = admin_client(make_admin(R.ADMINISTRATOR)).get(SECTION).context["rows"]
    assert "activities.marine_forecast_url" in {row["setting"].key for row in rows}


@pytest.mark.parametrize("role", [R.INSTRUCTOR, R.EQUIPMENT_MANAGER, R.BOARD])
def test_a_role_without_the_section_gets_not_found(make_admin, role):  # noqa: F811
    client = admin_client(make_admin(role))
    assert client.get(SECTION).status_code == 404
    detail = reverse("administration:setting_detail", args=["activities", OFFER])
    assert client.post(detail, {"value": "24", "note": "Prova"}).status_code == 404
    assert business_settings.get(OFFER) == 48


def test_the_manager_changes_the_offer_hours_on_the_screen(make_admin):  # noqa: F811
    client = admin_client(make_admin(R.COURSES_MANAGER))
    detail = reverse("administration:setting_detail", args=["activities", OFFER])
    client.post(detail, {"value": "6", "note": "Fora de rang"})  # de 12 a 168
    assert business_settings.get(OFFER) == 48
    assert client.post(detail, {"value": "24", "note": "Prova"}).status_code == 302
    assert business_settings.get(OFFER) == 24
    entry = AuditEntry.objects.get(action=business_settings.ACTION_CHANGED, field=OFFER)
    assert (entry.old_value, entry.new_value) == (48, 24)
