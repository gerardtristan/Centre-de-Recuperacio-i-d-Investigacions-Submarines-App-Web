"""Punts d'extensió del lloc i del cost de material estàndard (part de la T-M02-40; RN-M02-43;
RN-M03-23 i 25). Sense base de dades."""

import pytest
from django.core.exceptions import ImproperlyConfigured

from apps.activities import extensions


@pytest.fixture(autouse=True)
def clean_registries(monkeypatch):
    monkeypatch.setattr(extensions, "_place_sections", {})
    monkeypatch.setattr(extensions, "_material_cost", [])


def section(key="material.usual_centre", **extra):
    fields = {
        "key": key,
        "label": "Centre habitual",
        "fields": lambda place, viewer: {},
        "save": lambda place, data, by: None,
    }
    return extensions.PlaceSection(**{**fields, **extra})


def test_les_seccions_del_lloc_es_registren_en_ordre_i_amb_clau_unica():
    first, second = section(), section(key="altre.bloc")
    extensions.register_place_section(first)
    extensions.register_place_section(second)
    assert extensions.place_sections() == [first, second]
    with pytest.raises(ImproperlyConfigured):
        extensions.register_place_section(section())


@pytest.mark.parametrize(
    "bad",
    [
        object(),
        section(fields=None),
        section(save="no"),
        section(key=""),
        section(label=""),
    ],
)
def test_una_seccio_del_lloc_mal_feta_es_un_error_de_programacio(bad):
    with pytest.raises(ImproperlyConfigured):
        extensions.register_place_section(bad)


def test_sense_calculador_el_cost_estandard_queda_buit():
    assert extensions.standard_material_cost(object()) is None


def test_un_sol_calculador_del_cost_de_material():
    def calculator(activity):
        return 2500

    extensions.register_material_cost_calculator(calculator)
    extensions.register_material_cost_calculator(calculator)  # el mateix, dues vegades: res
    assert extensions.standard_material_cost(object()) == 2500
    with pytest.raises(ImproperlyConfigured):
        extensions.register_material_cost_calculator(lambda activity: 0)
    with pytest.raises(ImproperlyConfigured):
        extensions.register_material_cost_calculator("no")
