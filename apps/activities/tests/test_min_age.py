"""Edat mínima per fitxa i activitat (T-M02-32; addenda de la 058; RN-M02-33): prova amb dates
inventades, major, menor i sense data. Només dades inventades.
"""

import datetime

import pytest
from django.core.exceptions import ValidationError

from apps.activities import catalogue, duplicate, public, requirements, states
from apps.core.models import Person, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import a_course, a_person, an_entry, an_outing
from .helpers import moment as at

pytestmark = pytest.mark.django_db


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


@pytest.mark.parametrize(
    ("birth", "state", "allowed"),
    [
        (datetime.date(2011, 6, 14), requirements.MET, True),  # fa 16 anys el dia d'inici
        (datetime.date(2011, 6, 15), requirements.NOT_MET, False),  # els fa l'endemà
        (None, requirements.UNKNOWN, True),  # sense data: marcat, no bloqueja (RN-M01-55)
    ],
    ids=["major", "menor", "sense data"],
)
def test_rn_m02_33_minimum_age_on_the_start_day(manager, birth, state, allowed):
    person = a_person("Participant")
    Person.objects.filter(pk=person.pk).update(birth_date=birth)
    person.refresh_from_db()
    activity = an_outing(manager, min_age=16, requirements_mode="block")  # comença el 14/06/2027
    result = requirements.check(activity, person)
    (check,) = result.checks
    assert (check.key, check.state, result.allowed) == (requirements.AGE, state, allowed)
    assert check.flagged is (state == requirements.UNKNOWN)
    for private in ("2011", "15 anys"):  # mai la data ni l'edat
        assert private not in repr(result)


def test_a_course_copies_the_minimum_age_of_its_entry(manager):
    entry = an_entry(manager, min_age=14)
    assert a_course(manager, entry).min_age == 14
    assert a_course(manager, entry, min_age=18).min_age == 18
    assert catalogue.update_entry(entry, by=manager, min_age=None) == ["min_age"]
    entry.refresh_from_db()
    assert a_course(manager, entry).min_age is None


@pytest.mark.parametrize("wrong", [0, 100, True, "16"])
def test_wrong_minimum_ages_are_rejected_everywhere(manager, wrong):
    with pytest.raises(ValidationError):
        an_entry(manager, min_age=wrong)
    with pytest.raises(ValidationError):
        an_outing(manager, min_age=wrong)


def test_the_minimum_age_travels_with_the_copy_and_shows_on_the_public_page(manager):
    outing = an_outing(manager, min_age=16)
    assert duplicate.duplicate(outing, datetime.date(2028, 6, 13), by=manager).min_age == 16
    states.publish(outing, by=manager, now=at(2027, 6, 1, 9))
    assert public.get_activity(outing.pk, today=datetime.date(2027, 6, 1)).min_age == 16
