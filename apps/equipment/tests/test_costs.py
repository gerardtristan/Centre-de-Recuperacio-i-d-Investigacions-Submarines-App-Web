"""T-M03-27: cost de material estàndard d'una activitat (RN-M03-25; CA-M03-24). Només dades
inventades."""

import datetime

import pytest
from django.db import IntegrityError, transaction

from apps.activities import extensions
from apps.activities.models import Activity, OutingType, Place
from apps.activities.tests.helpers import outing_data
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment import costs
from apps.equipment.models import (
    CentreRate,
    DiveCentre,
    EquipmentType,
    PlaceUsualCentre,
    TypicalEquipmentTemplate,
    UsageRate,
)

pytestmark = pytest.mark.django_db
START = datetime.date(2027, 6, 14)


@pytest.fixture
def admin(make_admin):  # noqa: F811
    return make_admin("administrator")


@pytest.fixture
def place(admin):
    return Place.objects.create(name="Lloc de prova", created_by=admin)


@pytest.fixture
def activity(place):
    return Activity.objects.create(**outing_data(place))  # sortida d'un dia (14/6/2027)


def suit():
    return EquipmentType.objects.get(name="Neoprè")


def typical(quantity=1, equipment_type=None):
    return TypicalEquipmentTemplate.objects.create(
        outing_type=OutingType.objects.get(name="Immersió"),
        equipment_type=equipment_type or suit(),
        quantity_per_participant=quantity,
    )


def test_ca_m03_24_amb_la_tarifa_del_centre_habitual(activity, place, admin):
    typical()
    centre = DiveCentre.objects.create(name="Centre A")
    PlaceUsualCentre.objects.create(place=place, centre=centre, changed_by=admin)
    CentreRate.objects.create(centre=centre, label="Equip complet", equipment_type=suit(),
                              cost_cents=2500, member_price_cents=3000, valid_from=START,
                              created_by=admin)  # fmt: skip
    assert costs.standard_material_cost(activity) == 2500


def test_ca_m03_24_sense_tarifa_el_cost_d_us_per_dies(activity):
    typical()
    UsageRate.objects.create(equipment_type=suit(), cost_per_day_cents=200, valid_from=START)
    assert costs.standard_material_cost(activity) == 200
    Activity.objects.filter(pk=activity.pk).update(ends_on=START + datetime.timedelta(days=1))
    activity.refresh_from_db()
    assert costs.standard_material_cost(activity) == 400  # dos dies


def test_ca_m03_24_sense_material_tipic_zero(activity):
    assert costs.standard_material_cost(activity) == 0
    assert extensions.standard_material_cost(activity) == 0  # el calculador registrat al 02


def test_sense_cost_d_us_vigent_zero_i_es_suma_per_linia(activity):
    typical(quantity=2)
    typical(equipment_type=EquipmentType.objects.get(name="Ampolla"))
    UsageRate.objects.create(
        equipment_type=suit(), cost_per_day_cents=150, valid_from=START + datetime.timedelta(days=1)
    )  # encara no vigent
    assert costs.standard_material_cost(activity) == 0
    UsageRate.objects.create(equipment_type=suit(), cost_per_day_cents=100, valid_from=START)
    assert costs.standard_material_cost(activity) == 200  # 2 × 100 × 1; l'ampolla, 0


def test_un_curs_fa_servir_el_material_de_la_seva_fitxa(place):
    from apps.activities.models import TrainingCatalogueEntry

    data = outing_data(place, kind=Activity.Kind.COURSE, outing_type=None, place=None)
    entry = TrainingCatalogueEntry.objects.create(
        kind="course",
        name="Curs inventat",
        default_places=8,
        price_member_cents=0,
        price_non_member_cents=0,
        department=data["department"],
    )
    course = Activity.objects.create(**{**data, "catalogue_entry": entry})
    TypicalEquipmentTemplate.objects.create(
        catalogue_entry=entry, equipment_type=suit(), quantity_per_participant=1
    )
    UsageRate.objects.create(equipment_type=suit(), cost_per_day_cents=300, valid_from=START)
    assert costs.standard_material_cost(course) == 300  # sense lloc: el cost d'ús


def test_restriccions(admin):
    with pytest.raises(IntegrityError), transaction.atomic():
        TypicalEquipmentTemplate.objects.create(equipment_type=suit(), quantity_per_participant=1)
    typical_row = typical()
    assert str(typical_row) == "Neoprè × 1"
    rate = UsageRate.objects.create(equipment_type=suit(), cost_per_day_cents=1, valid_from=START)
    assert str(rate) == "Neoprè: 1 c/dia"
    with pytest.raises(IntegrityError), transaction.atomic():
        UsageRate.objects.create(equipment_type=suit(), cost_per_day_cents=2, valid_from=START)
