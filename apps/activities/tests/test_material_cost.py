"""Cost de material previst (part de servei de la T-M02-40; RN-M02-43; CA-M02-45; AC23). Només
dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.activities import material_cost
from apps.activities.models import OutingType
from apps.core.models import AuditEntry, Charge, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment.models import EquipmentType, TypicalEquipmentTemplate, UsageRate

from .helpers import TODAY, a_person, an_outing

pytestmark = pytest.mark.django_db
R = Role.Code


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(R.COURSES_MANAGER)


def with_typical_material(cost_per_day=1250):  # sortida de dos dies: 2500
    suit = EquipmentType.objects.get(name="Neoprè")
    TypicalEquipmentTemplate.objects.create(
        outing_type=OutingType.objects.get(name="Immersió"), equipment_type=suit,
        quantity_per_participant=1,
    )  # fmt: skip
    UsageRate.objects.create(equipment_type=suit, cost_per_day_cents=cost_per_day, valid_from=TODAY)


def test_rn_m02_43_a_new_activity_copies_the_standard_from_the_03(manager):
    with_typical_material()
    activity = an_outing(manager)
    activity.refresh_from_db()
    assert (activity.standard_material_cost_cents, activity.material_cost_cents) == (2500, 2500)


def test_ca_m02_45_a_different_cost_needs_a_note_and_is_logged(make_admin):  # noqa: F811
    with_typical_material()
    treasurer = make_admin(R.TREASURER)
    activity = an_outing(make_admin(R.COURSES_MANAGER))
    charges_before = Charge.objects.count()
    with pytest.raises(ValidationError):
        material_cost.set_material_cost(activity, 1800, by=treasurer)
    material_cost.set_material_cost(activity, 1800, by=treasurer, note="Centre amb descompte.")
    activity.refresh_from_db()
    assert (activity.material_cost_cents, activity.material_cost_note) == (
        1800, "Centre amb descompte.",
    )  # fmt: skip
    entry = AuditEntry.objects.get(action=material_cost.MATERIAL_COST_CHANGED)
    assert (entry.old_value, entry.new_value) == (2500, 1800)
    assert Charge.objects.count() == charges_before  # cap càrrec
    material_cost.set_material_cost(activity, 2500, by=treasurer)  # l'estàndard, sense nota
    with pytest.raises(ValidationError):
        material_cost.set_material_cost(activity, -1, by=treasurer, note="x")


def test_ac23_own_activities_for_the_manager_and_nothing_for_an_instructor(make_admin):  # noqa: F811
    person = a_person("Responsable inventada")
    responsible = make_admin(R.COURSES_MANAGER, person=person)
    own, other = an_outing(responsible, responsible=person), an_outing(responsible)
    material_cost.set_material_cost(own, 0, by=responsible)
    for who, activity in ((responsible, other), (make_admin(R.INSTRUCTOR), own)):
        with pytest.raises(Http404):
            material_cost.set_material_cost(activity, 0, by=who)
