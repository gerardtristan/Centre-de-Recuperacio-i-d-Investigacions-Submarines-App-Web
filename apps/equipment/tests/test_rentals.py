"""T-M03-10: llista de lloguer per centre (RN-M03-18; CA-M03-07; MT9). Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.activities.tests.test_attendance import enrolled
from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment import assignments, rentals
from apps.equipment.models import CentreRate, DiveCentre, EquipmentNeed, RentalList

from .test_assignments import JUNE, keeper, kind, manager, outing  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db


@pytest.fixture
def centre(keeper):  # noqa: F811
    centre = DiveCentre.objects.create(name="Centre A")
    for name in ("Jaquet", "Neoprè"):
        CentreRate.objects.create(
            centre=centre, label=name, equipment_type=kind(name), cost_cents=2500,
            member_price_cents=3000, valid_from=JUNE, created_by=keeper,
        )  # fmt: skip
    return centre


def rent(activity, centre, keeper, first, name, size):  # noqa: F811
    row = enrolled(activity, first)
    EquipmentNeed.objects.create(
        enrolment=row, equipment_type=kind(name), brings_own=False, size=size
    )
    assignments.assign_rented(row, kind(name), centre, by=keeper)
    return row


def test_ca_m03_07_grouped_with_references_not_names_and_not_stored(manager, keeper, centre):  # noqa: F811
    activity = outing(manager)
    a = rent(activity, centre, keeper, "Anna", "Jaquet", "M")
    b = rent(activity, centre, keeper, "Bernat", "Jaquet", "M")
    c = rent(activity, centre, keeper, "Carla", "Jaquet", "L")
    d = rent(activity, centre, keeper, "Dídac", "Neoprè", "M")
    content = rentals.generate(activity, centre, by=keeper)
    assert content.lines == (
        ("Jaquet", "L", 1, (f"{c.pk}-CP",)),
        ("Jaquet", "M", 2, tuple(sorted((f"{a.pk}-AP", f"{b.pk}-BP")))),
        ("Neoprè", "M", 1, (f"{d.pk}-DP",)),
    )
    text = rentals.to_csv(content)
    assert "Anna" not in text and "Prova" not in text and "@" not in text
    saved = RentalList.objects.get()
    assert {f.name for f in RentalList._meta.get_fields()} >= {"fingerprint"}
    assert not any("line" in f.name for f in RentalList._meta.get_fields())  # no es desa
    entry = AuditEntry.objects.get(action=rentals.GENERATED)
    assert entry.details["fingerprint"] == saved.fingerprint == content.rental_list.fingerprint


def test_mark_sent_once_and_only_the_latest_list_counts(manager, keeper, centre):  # noqa: F811
    activity = outing(manager)
    rent(activity, centre, keeper, "Anna", "Jaquet", "M")
    first = rentals.generate(activity, centre, by=keeper).rental_list
    second = rentals.generate(activity, centre, by=keeper).rental_list
    assert first.fingerprint == second.fingerprint  # el mateix contingut
    assert rentals.unsent(activity) == [second]
    rentals.mark_sent(second, by=keeper)
    assert rentals.unsent(activity) == []
    with pytest.raises(ValidationError):
        rentals.mark_sent(second, by=keeper)


def test_mt9_by_role(manager, keeper, centre, make_admin):  # noqa: F811
    activity = outing(manager)
    with pytest.raises(Http404):
        rentals.generate(activity, centre, by=make_admin(Role.Code.SECRETARY))
    rentals.generate(activity, centre, by=manager)  # el responsable de cursos i sortides
