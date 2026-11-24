"""Catàleg d'indicadors del dashboard (T-M08-02; CA-M08-05; RN-M08-03; P-488)."""

import importlib

import pytest
from django.urls import reverse

from apps.core import business_settings, permissions
from apps.core.models import Setting
from apps.dashboard import indicators
from apps.dashboard.indicators import CATALOG, Indicator, InvalidIndicator

VALID = {
    "code": "example",
    "panels": ("general",),
    "name": "Exemple",
    "definition": "Recompte inventat.",
    "source": "members.stats",
    "unit": "count",
    "kind": "people",
}


def test_ca_m08_05_every_indicator_has_panel_definition_source_unit_and_kind():
    assert CATALOG
    for code, indicator in CATALOG.items():
        assert indicator.code == code
        assert indicator.panels and set(indicator.panels) <= indicators.PANELS.keys()
        assert str(indicator.name).strip() and str(indicator.definition).strip()
        assert indicator.source and indicator.unit in indicators.UNITS
        assert indicator.kind in indicators.KINDS


def test_every_panel_has_indicators():
    used = {panel for indicator in CATALOG.values() for panel in indicator.panels}
    assert used == indicators.PANELS.keys()


@pytest.mark.parametrize(
    "field, value",
    [
        ("definition", ""),
        ("definition", "   "),
        ("name", ""),
        ("source", ""),
        ("panels", ()),
        ("panels", ("unknown",)),
        ("unit", "euros"),
        ("kind", "health"),
        ("code", "Bad-Code"),
        ("code", "x" * (indicators.CODE_MAX_LENGTH + 1)),
        ("detail_permission", "members.list"),  # sense ruta
        ("detail_route", "administration:members_list"),  # sense permís
    ],
)
def test_ca_m08_05_an_incomplete_indicator_cannot_be_registered(field, value):
    with pytest.raises(InvalidIndicator):
        Indicator(**{**VALID, field: value})


def test_a_repeated_code_cannot_be_registered():
    with pytest.raises(InvalidIndicator):
        indicators._catalog(Indicator(**VALID), Indicator(**VALID))


def test_money_is_the_only_kind_in_cents_and_cents_are_money():
    # RN-M08-02 no s'aplica als imports: un import mai no passa per la supressió de persones.
    for indicator in CATALOG.values():
        assert (indicator.unit == "cents") == (indicator.kind == "money"), indicator.code


@pytest.mark.django_db
def test_every_detail_link_is_a_catalog_permission_and_a_route():
    # RN-M08-05: el bloc enllaça només amb un permís que existeix; el mòdul el torna a comprovar.
    for indicator in CATALOG.values():
        if indicator.detail_permission:
            assert indicator.detail_permission in permissions.CATALOG, indicator.code
            assert reverse(indicator.detail_route).startswith("/gestio/"), indicator.code


@pytest.mark.django_db
def test_p488_every_indicator_has_an_empty_help_text_setting():
    for indicator in CATALOG.values():
        setting = Setting.objects.get(key=indicator.help_key)
        assert (setting.module, setting.value_type, setting.initial_value) == (
            "dashboard", "text", "",
        )  # fmt: skip
        assert indicator.help_text() == ""


def test_the_migration_creates_exactly_the_catalog_codes():
    migration = importlib.import_module("apps.dashboard.migrations.0001_help_texts")
    assert sorted(migration.CODES) == sorted(CATALOG)


@pytest.mark.django_db
def test_p488_the_help_text_is_the_setting_and_the_definition_stays(monkeypatch):
    indicator = CATALOG["active_members"]
    values = {indicator.help_key: "Inclou els socis d'honor."}
    monkeypatch.setattr(business_settings, "get", lambda key, at=None: values[key])
    assert indicator.help_text() == "Inclou els socis d'honor."
    assert str(indicator.definition) == "Socis amb l'estat «actiu» el darrer dia del període."


def test_the_help_text_family_names_each_row_after_the_indicator():
    assert business_settings.family_of("dashboard.help_text.retention") == indicators.HELP_TEXT
    assert indicators.name_of("retention") == "Retenció"
    assert indicators.name_of("unknown") == "unknown"
