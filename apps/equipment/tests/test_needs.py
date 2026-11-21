"""T-M03-07: bloc del formulari d'inscripció i necessitats (P-M03-C; HU-M03-04; MT1). Només dades
inventades."""

import pytest
from django.core.exceptions import ValidationError

from apps.activities import enrolment, extensions
from apps.activities.models import Enrolment, OutingType
from apps.activities.tests.helpers import BEFORE_DEADLINE, a_member, an_open_outing
from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment import needs
from apps.equipment.models import EquipmentNeed, EquipmentType, TypicalEquipmentTemplate

pytestmark = pytest.mark.django_db


def kind(name):
    return EquipmentType.objects.get(name=name)


@pytest.fixture
def outing(make_admin):  # noqa: F811
    """Sortida d'immersió amb jaquet (talla), ampolla (litres) i ploms (sense mida) típics."""
    for name in ("Jaquet", "Ampolla", "Ploms"):
        TypicalEquipmentTemplate.objects.create(
            outing_type=OutingType.objects.get(name="Immersió"), equipment_type=kind(name),
            quantity_per_participant=1,
        )  # fmt: skip
    return an_open_outing(make_admin(Role.Code.COURSES_MANAGER))


def enrol(activity, answers, first="Sòcia"):
    account = a_member(first)
    return enrolment.enrol(
        activity, account.person, channel="account", actor=account,
        answers={needs.SECTION_KEY: answers}, now=BEFORE_DEADLINE,
    )  # fmt: skip


def test_the_03_registers_its_block_with_one_question_per_typical_type(outing):
    section = next(s for s in extensions.enrolment_sections() if s.key == needs.SECTION_KEY)
    fields = section.fields(outing, None)
    jacket, tank, weights = kind("Jaquet").pk, kind("Ampolla").pk, kind("Ploms").pk
    assert set(fields) == {
        f"need_{jacket}",
        f"size_{jacket}",
        f"need_{tank}",
        f"litres_{tank}",
        f"need_{weights}",
    }


def test_hu_m03_04_needs_are_saved_with_the_enrolment(outing):
    jacket, tank, weights = kind("Jaquet").pk, kind("Ampolla").pk, kind("Ploms").pk
    row = enrol(outing, {
        f"need_{jacket}": "need", f"size_{jacket}": " M ",
        f"need_{tank}": "need", f"litres_{tank}": 12,
        f"need_{weights}": "own",
    })  # fmt: skip
    saved = {
        n.equipment_type.name: (n.brings_own, n.size, n.litres) for n in needs.needs_of(outing)
    }
    assert saved == {
        "Jaquet": (False, "M", None),
        "Ampolla": (False, "", 12),
        "Ploms": (True, "", None),
    }
    assert all(n.enrolment_id == row.pk for n in needs.needs_of(outing))


def test_a_needed_piece_needs_its_size_and_nothing_is_saved_otherwise(outing):
    jacket = kind("Jaquet").pk
    with pytest.raises(ValidationError):
        enrol(outing, {f"need_{jacket}": "need"})
    assert not Enrolment.objects.exists() and not EquipmentNeed.objects.exists()
    with pytest.raises(ValidationError):  # un tipus que no és de l'activitat
        enrol(outing, {f"need_{kind('Aletes').pk}": "need", f"size_{kind('Aletes').pk}": "42"})
    with pytest.raises(ValidationError):
        enrol(outing, {f"need_{jacket}": "potser"})
    row = enrol(outing, {f"need_{jacket}": "own"})  # si el porta, la talla no cal
    assert EquipmentNeed.objects.get(enrolment=row).brings_own


def test_a_waitlisted_enrolment_keeps_its_needs(outing):
    jacket = kind("Jaquet").pk
    outing.max_places = 1
    outing.save(update_fields=["max_places"])
    enrol(outing, {f"need_{jacket}": "own"}, "Primera")
    second = enrol(outing, {f"need_{jacket}": "need", f"size_{jacket}": "L"}, "Segona")
    assert second.status == Enrolment.Status.WAITLISTED
    assert EquipmentNeed.objects.get(enrolment=second).size == "L"
