import datetime

import pytest

from apps.licences.models import Licence, LicenceType, ValidityRule


@pytest.fixture
def annual(db):
    return LicenceType.objects.create(
        name="Aficionat anual (inventat)",
        category=LicenceType.Category.AMATEUR,
        validity_rule=ValidityRule.CALENDAR_YEAR,
    )


@pytest.fixture
def make_licence(make_person, annual):
    person = make_person()

    def make(**fields):
        values = {
            "person": person,
            "licence_type": annual,
            "validity_rule": annual.validity_rule,
            "status": Licence.Status.REQUESTED,
            "origin": Licence.Origin.CLUB,
            "starts_on": datetime.date(2027, 3, 15),
            "expires_on": datetime.date(2027, 12, 31),
            "price_kind": "member",
            "price_cents": 9000,
        }
        values.update(fields)
        return Licence.objects.create(**values)

    return make
