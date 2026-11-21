"""T-M03-06: material típic, còpia en crear i en duplicar una activitat (RN-M03-17; CA-M03-10).
Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.activities import extensions
from apps.activities.models import Activity, OutingType, Place
from apps.activities.tests.helpers import outing_data
from apps.core.models import AuditEntry
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment import access, typical
from apps.equipment.models import (
    ActivityTypicalEquipment,
    EquipmentType,
    TypicalEquipmentTemplate,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def manager(make_admin):  # noqa: F811
    # MT5 de la matriu inicial (T-M03-18).
    return make_admin("equipment_manager")


@pytest.fixture
def place(manager):
    return Place.objects.create(name="Lloc de prova", created_by=manager)


def dive():
    return OutingType.objects.get(name="Immersió")


def kind(name):
    return EquipmentType.objects.get(name=name)


def lines(activity):
    return {
        (row.equipment_type.name, row.quantity_per_participant)
        for row in ActivityTypicalEquipment.objects.filter(activity=activity)
    }


def test_en_crear_l_activitat_es_copia_la_plantilla(manager, place):
    typical.set_template_line(kind("Neoprè"), 1, by=manager, outing_type=dive())
    typical.set_template_line(kind("Ampolla"), 2, by=manager, outing_type=dive())
    activity = Activity.objects.create(**outing_data(place))
    assert lines(activity) == {("Neoprè", 1), ("Ampolla", 2)}
    assert set(typical.lines_for(activity)) == {(kind("Neoprè"), 1), (kind("Ampolla"), 2)}


def test_ca_m03_10_la_copia_te_el_material_de_l_original(manager, place):
    typical.set_template_line(kind("Neoprè"), 1, by=manager, outing_type=dive())
    original = Activity.objects.create(**outing_data(place))
    typical.set_activity_line(original, kind("Jaquet"), 1, by=manager)
    typical.set_activity_line(original, kind("Neoprè"), 0, by=manager)  # treu la línia
    assert typical.set_activity_line(original, kind("Aletes"), 0, by=manager) is None
    copy = Activity.objects.create(**outing_data(place))  # en crear-la, la plantilla
    extensions.activity_duplicated.send(sender=Activity, original=original, copy=copy, by=manager)
    assert lines(copy) == {("Jaquet", 1)}
    assert str(ActivityTypicalEquipment.objects.get(activity=copy)) == "Jaquet × 1"


def test_una_copia_de_la_plantilla_no_es_repeteix(manager, place):
    typical.set_template_line(kind("Neoprè"), 1, by=manager, outing_type=dive())
    activity = Activity.objects.create(**outing_data(place))
    typical.copy_from_template(activity)
    activity.save()  # desar-la de nou no torna a copiar res
    assert ActivityTypicalEquipment.objects.filter(activity=activity).count() == 1


def test_canviar_la_plantilla_queda_al_registre_i_amb_zero_es_treu(manager):
    typical.set_template_line(kind("Aletes"), 1, by=manager, outing_type=dive())
    typical.set_template_line(kind("Aletes"), 2, by=manager, outing_type=dive())
    assert TypicalEquipmentTemplate.objects.get().quantity_per_participant == 2
    assert typical.set_template_line(kind("Aletes"), 0, by=manager, outing_type=dive()) is None
    assert typical.set_template_line(kind("Aletes"), 0, by=manager, outing_type=dive()) is None
    assert not TypicalEquipmentTemplate.objects.exists()
    values = list(
        AuditEntry.objects.filter(action=typical.TEMPLATE_CHANGED)
        .order_by("pk")
        .values_list("old_value", "new_value")
    )
    assert values == [(0, 1), (1, 2), (2, 0), (0, 0)]


@pytest.mark.parametrize("quantity", [-1, 101, 1.5, True])
def test_quantitats_que_no_valen(manager, quantity):
    with pytest.raises(ValidationError):
        typical.set_template_line(kind("Aletes"), quantity, by=manager, outing_type=dive())


def test_la_plantilla_es_d_una_fitxa_o_d_un_tipus(manager):
    with pytest.raises(ValidationError):
        typical.set_template_line(kind("Aletes"), 1, by=manager)


def test_sense_mt5_no_es_toca(make_admin, place):  # noqa: F811
    secretary = make_admin("secretary")
    with pytest.raises(Http404):
        typical.set_template_line(kind("Aletes"), 1, by=secretary, outing_type=dive())
    activity = Activity.objects.create(**outing_data(place))
    with pytest.raises(Http404):
        typical.set_activity_line(activity, kind("Aletes"), 1, by=secretary)


def test_access_nomes_amb_un_codi_del_cataleg(make_admin):  # noqa: F811
    assert access.allowed(make_admin("administrator"), "equipment.no_existeix") is False
    with pytest.raises(Http404):
        access.require(make_admin("administrator"), "equipment.no_existeix")
