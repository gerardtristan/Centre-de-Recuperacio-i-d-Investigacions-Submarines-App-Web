"""T-M03-02: tipus de material i dades inicials; mida segons el tipus (RN-M03-05; CA-M03-01).
Només dades inventades."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.equipment.measures import clean_measure
from apps.equipment.models import EquipmentType

pytestmark = pytest.mark.django_db


def kind(name):
    return EquipmentType.objects.get(name=name)


def test_els_14_tipus_inicials_de_f_6():
    assert EquipmentType.objects.filter(active=True).count() == 14
    assert (kind("Ampolla").sizing, kind("Ampolla").requires_review) == ("litres", True)
    assert (kind("Jaquet").sizing, kind("Regulador").requires_review) == ("size", True)
    assert str(kind("Màscara")) == "Màscara"


def test_un_tipus_nou_es_una_dada_amb_nom_unic():
    EquipmentType.objects.create(name="Capucha", sizing="size")
    with pytest.raises(IntegrityError), transaction.atomic():
        EquipmentType.objects.create(name="Capucha", sizing="size")
    with pytest.raises(IntegrityError), transaction.atomic():
        EquipmentType.objects.create(name="Cinturó", sizing="kg")


@pytest.mark.parametrize("litres", [None, 0, "0", -12, "11.55", "tretze", "Infinity", "NaN", 1e30])
def test_ca_m03_01_una_ampolla_sense_litres_valids_es_rebutja(litres):
    with pytest.raises(ValidationError):
        clean_measure(kind("Ampolla"), litres=litres)


@pytest.mark.parametrize(("litres", "expected"), [(12, "12.0"), ("11.5", "11.5"), (15.0, "15.0")])
def test_ca_m03_01_una_ampolla_amb_12_o_11_5_s_accepta(litres, expected):
    assert clean_measure(kind("Ampolla"), litres=litres) == ("", Decimal(expected))


def test_talla_nomes_on_toca():
    assert clean_measure(kind("Jaquet"), size=" M ") == ("M", None)
    assert clean_measure(kind("Màscara")) == ("", None)
    for args in (
        (kind("Jaquet"), ""),
        (kind("Jaquet"), "x" * 11),
        (kind("Màscara"), "M"),
        (kind("Ampolla"), "M", 12),
    ):
        with pytest.raises(ValidationError):
            clean_measure(*args)
    with pytest.raises(ValidationError):
        clean_measure(kind("Jaquet"), "M", 12)
