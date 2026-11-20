"""Llistat de la secretaria, filtres i venciments (T-M06-09; HU-M06-05; LC4, C6; CA-M06-33)."""

import datetime

import pytest
from django.http import Http404

from apps.core.models import Role, RolePermission
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.licences.listing import expiring, licence_list
from apps.licences.models import Licence, LicenceType, ValidityRule

D = datetime.date
R = Role.Code
TODAY = D(2027, 11, 2)
EXT = {"origin": "external", "price_kind": None, "price_cents": None, "status": "active"}


@pytest.fixture
def licences(make_licence, make_person, annual):
    technical = LicenceType.objects.create(
        name="Tècnic anual (inventat)", category="technical", validity_rule="calendar_year"
    )
    return {
        "to_renew": make_licence(
            person=make_person("Anna", "Vila"), federation_number="F-1", **EXT
        ),
        "valid": make_licence(
            person=make_person("Pere", "Roca"), licence_type=technical,
            starts_on=D(2027, 6, 1), expires_on=D(2028, 5, 31), **EXT,
        ),
        "requested": make_licence(person=make_person("Eva", "Mas")),
        "expired": make_licence(
            person=make_person("Joan", "Bosch"), starts_on=D(2026, 1, 1),
            expires_on=D(2026, 12, 31), **EXT,
        ),
        "day": make_licence(
            person=make_person("Laia", "Font"), validity_rule=ValidityRule.SINGLE_DAY,
            starts_on=D(2027, 11, 20), expires_on=D(2027, 11, 20), **EXT,
        ),
    }  # fmt: skip


def names(rows):
    return [row.person_name for row in rows]


def test_the_secretary_sees_every_licence_with_its_shown_status(make_admin, licences):  # noqa: F811
    rows = licence_list(make_admin(R.SECRETARY), today=TODAY)
    assert names(rows) == ["Bosch, Joan", "Font, Laia", "Mas, Eva", "Roca, Pere", "Vila, Anna"]
    by_name = {row.person_name: row for row in rows}
    assert by_name["Vila, Anna"].status == Licence.Display.TO_RENEW
    assert by_name["Roca, Pere"].status == Licence.Display.VALID
    assert by_name["Mas, Eva"].status == Licence.Display.REQUESTED
    assert by_name["Bosch, Joan"].status == Licence.Display.EXPIRED
    vila = by_name["Vila, Anna"]
    assert (vila.category, vila.expires_on, vila.federation_number) == (
        "amateur",
        D(2027, 12, 31),
        "F-1",
    )
    assert by_name["Mas, Eva"].federation_number is None


def test_filters(make_admin, licences, annual):  # noqa: F811
    secretary = make_admin(R.SECRETARY)
    assert names(licence_list(secretary, today=TODAY, category="technical")) == ["Roca, Pere"]
    assert names(licence_list(secretary, today=TODAY, licence_type=annual, status="expired")) == [
        "Bosch, Joan"
    ]
    assert names(licence_list(secretary, today=TODAY, status="to_renew")) == ["Vila, Anna"]


@pytest.mark.parametrize(("days", "expected"), [(7, []), (30, []), (60, ["Vila, Anna"])])
def test_expiring_within_60_30_and_7_days(make_admin, licences, days, expected):  # noqa: F811
    rows = licence_list(make_admin(R.SECRETARY), today=TODAY, expiring_within=days)
    assert names(rows) == expected


def test_expiring_is_ordered_and_leaves_out_single_day_and_expired(
    licences, make_licence, make_person
):
    make_licence(person=make_person("Abel", "Vila"), federation_number="F-2", **EXT)
    found = expiring(400, today=TODAY)
    assert [(lic.person.last_name, lic.person.first_name) for lic in found] == [
        ("Vila", "Abel"), ("Vila", "Anna"), ("Roca", "Pere"),
    ]  # fmt: skip


@pytest.mark.parametrize("role", [R.COURSES_MANAGER, R.TREASURER, R.PRESIDENT, R.ADMINISTRATOR])
def test_every_lc4_role_sees_the_list(make_admin, licences, role):  # noqa: F811
    assert len(licence_list(make_admin(role), today=TODAY)) == 5


@pytest.mark.parametrize("role", [R.INSTRUCTOR, R.EQUIPMENT_MANAGER, R.BOARD, None])
def test_without_lc4_not_found(make_admin, licences, role):  # noqa: F811
    with pytest.raises(Http404):
        licence_list(make_admin(*([role] if role else [])), today=TODAY)


def test_without_c6_no_number_category_or_expiry(make_admin, licences):  # noqa: F811
    RolePermission.objects.filter(
        role__code=R.SECRETARY, permission_code="licences.field.details"
    ).delete()
    secretary = make_admin(R.SECRETARY)
    rows = licence_list(secretary, today=TODAY)
    assert {(row.category, row.expires_on, row.federation_number) for row in rows} == {
        (None, None, None)
    }
    for forced in ({"category": "technical"}, {"expiring_within": 60}):
        with pytest.raises(Http404):
            licence_list(secretary, today=TODAY, **forced)


def test_the_row_never_carries_birth_date_or_document(make_admin, licences):  # noqa: F811
    (row, *_) = licence_list(make_admin(R.SECRETARY), today=TODAY)
    assert not {"birth_date", "id_document_number", "document"} & set(row.__dataclass_fields__)
