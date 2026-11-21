"""T-M03-03: inventari de peces, estats, baixa i historial (RN-M03-04 i 05; CA-M03-01). Només
dades inventades."""

import datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404

from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment import access, inventory
from apps.equipment.models import EquipmentItem, EquipmentType

pytestmark = pytest.mark.django_db
REVIEW = datetime.date(2027, 9, 1)


@pytest.fixture
def manager(make_admin, monkeypatch):  # noqa: F811
    monkeypatch.setattr(access, "allowed", lambda by, code, obj=None: True)  # MT3 (T-M03-18)
    return make_admin("equipment_manager")


def kind(name):
    return EquipmentType.objects.get(name=name)


def tank(by, **extra):
    fields = {"equipment_type": kind("Ampolla"), "litres": 12, "next_review_on": REVIEW, "by": by}
    return inventory.create_item(**{**fields, **extra})


def test_alta_amb_el_codi_seguent_i_la_mida_del_tipus(manager):
    first = tank(manager)
    second = inventory.create_item(equipment_type=kind("Jaquet"), size="M", by=manager)
    assert (first.code, first.litres, str(first)) == ("MAT-0001", Decimal("12.0"), "MAT-0001")
    assert (second.code, second.size, second.status) == ("MAT-0002", "M", "available")
    EquipmentItem.objects.create(code="ANTIC-1", type=kind("Màscara"))  # un codi d'un altre format
    assert inventory.next_code() == "MAT-0003"
    assert inventory.history(first).first().action == inventory.ITEM_CREATED


@pytest.mark.parametrize(
    "extra",
    [
        {"litres": 0},  # CA-M03-01
        {"litres": None},
        {"next_review_on": None},  # l'ampolla porta la revisió
        {"purchase_cost_cents": -1},
        {"purchase_cost_cents": 12.5},
        {"code": "x" * 21},
    ],
)
def test_alta_que_no_val(manager, extra):
    with pytest.raises(ValidationError):
        tank(manager, **extra)
    assert not EquipmentItem.objects.exists()


def test_codi_unic_tipus_actiu_i_camps_coneguts(manager):
    tank(manager, code="MAT-0007")
    with pytest.raises(ValidationError):
        tank(manager, code="MAT-0007")
    closed = EquipmentType.objects.create(name="Capucha", sizing="size", active=False)
    with pytest.raises(ValidationError):
        inventory.create_item(equipment_type=closed, size="M", by=manager)
    with pytest.raises(TypeError):
        inventory.create_item(equipment_type=kind("Màscara"), status="retired", by=manager)


def test_editar_queda_a_l_historial_amb_el_valor_anterior(manager):
    item = tank(manager)
    inventory.update_item(
        item, by=manager, litres="15", notes=" Revisada ", next_review_on=datetime.date(2028, 9, 1)
    )
    item.refresh_from_db()
    assert (item.litres, item.notes) == (Decimal("15.0"), "Revisada")
    changes = {(e.field, e.old_value, e.new_value) for e in inventory.history(item) if e.field}
    assert ("litres", "12.0", "15.0") in changes
    assert ("next_review_on", "2027-09-01", "2028-09-01") in changes
    with pytest.raises(TypeError):
        inventory.update_item(item, by=manager, code="MAT-9999")


def test_estats_i_baixa_amb_motiu(manager):
    item = tank(manager)
    inventory.change_status(item, "in_review", by=manager)
    inventory.change_status(item, "available", by=manager)
    with pytest.raises(ValidationError):
        inventory.change_status(item, "retired", by=manager)  # sense motiu
    retired = inventory.change_status(item, "retired", by=manager, reason="Perduda")
    assert (retired.status, retired.retired_reason) == ("retired", "Perduda")
    with pytest.raises(ValidationError):
        inventory.change_status(item, "available", by=manager)  # una baixa no torna
    with pytest.raises(ValidationError):
        inventory.update_item(item, by=manager, notes="Trobada")
    statuses = [(e.old_value, e.new_value) for e in inventory.history(item) if e.field == "status"]
    assert statuses == [
        ("available", "in_review"),
        ("in_review", "available"),
        ("available", "retired"),
    ]


def test_sense_mt3_no_es_toca(make_admin, monkeypatch):  # noqa: F811
    monkeypatch.setattr(access, "allowed", lambda by, code, obj=None: False)
    secretary = make_admin("secretary")
    with pytest.raises(Http404):
        inventory.create_item(equipment_type=kind("Màscara"), by=secretary)
    item = EquipmentItem.objects.create(code="MAT-0001", type=kind("Màscara"))
    with pytest.raises(Http404):
        inventory.update_item(item, by=secretary, notes="x")
    with pytest.raises(Http404):
        inventory.change_status(item, "in_review", by=secretary)


@pytest.mark.parametrize(
    "fields",
    [
        {"status": "lost"},
        {"litres": 0},
        {"status": "retired"},  # sense motiu
        {"code": ""},
    ],
)
def test_restriccions_de_la_base_de_dades(fields):
    with pytest.raises(IntegrityError), transaction.atomic():
        EquipmentItem.objects.create(**{"code": "MAT-0001", "type": kind("Màscara"), **fields})
