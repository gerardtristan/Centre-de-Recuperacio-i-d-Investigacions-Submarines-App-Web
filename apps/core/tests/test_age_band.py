"""`Person.birth_date` i `persons.age_band` (058; RN-M01-48, RN-M01-55; T-M01-33).

Límits: aniversari dels 18, 29 de febrer, data futura o buida i data local de Barcelona.
Només dades inventades.
"""

from datetime import UTC, date, datetime
from unittest import mock

import pytest

from apps.core.models import Person
from apps.core.persons import AgeBand, age_band

ON = date(2026, 11, 9)


def person(birth_date):
    return Person(first_name="Anna", origin=Person.Origin.WEB, birth_date=birth_date)


@pytest.mark.django_db
def test_birth_date_is_optional_and_stored():
    without = Person.objects.create(first_name="Pau", origin=Person.Origin.WEB)
    with_date = Person.objects.create(
        first_name="Laia", origin=Person.Origin.WEB, birth_date=date(1988, 10, 8)
    )
    assert Person.objects.get(pk=without.pk).birth_date is None
    assert Person.objects.get(pk=with_date.pk).birth_date == date(1988, 10, 8)


@pytest.mark.parametrize(
    ("birth", "on", "band"),
    [
        # 18 anys: el dia abans, menor; el mateix dia, major.
        (date(2008, 11, 10), ON, AgeBand.MINOR),
        (date(2008, 11, 9), ON, AgeBand.ADULT),
        (date(2008, 11, 8), ON, AgeBand.ADULT),
        # Canvi d'any: 31/12 i 01/01.
        (date(2008, 1, 1), date(2025, 12, 31), AgeBand.MINOR),
        (date(2008, 1, 1), date(2026, 1, 1), AgeBand.ADULT),
        # 29 de febrer: els 18 mai cauen en un any de traspàs; es compleixen l'1 de març.
        (date(2008, 2, 29), date(2026, 2, 28), AgeBand.MINOR),
        (date(2008, 2, 29), date(2026, 3, 1), AgeBand.ADULT),
        # Nascut el 28 de febrer i any de traspàs: el 28, no el 29.
        (date(2010, 2, 28), date(2028, 2, 27), AgeBand.MINOR),
        (date(2010, 2, 28), date(2028, 2, 28), AgeBand.ADULT),
        # Nascut avui: menor (0 anys), no desconegut.
        (ON, ON, AgeBand.MINOR),
        (date(1930, 5, 1), ON, AgeBand.ADULT),
    ],
)
def test_age_band_boundaries(birth, on, band):
    assert age_band(person(birth), on) == band


@pytest.mark.parametrize("birth", [None, date(2026, 11, 10), date(2030, 1, 1)])
def test_empty_or_future_birth_date_is_unknown(birth):
    assert age_band(person(birth), ON) == AgeBand.UNKNOWN


def test_default_day_is_today_in_barcelona():
    # 09/03/2026 a les 23:30 UTC ja és el 10/03 a Barcelona: els 18 ja s'han complert.
    now = datetime(2026, 3, 9, 23, 30, tzinfo=UTC)
    with mock.patch("django.utils.timezone.now", return_value=now):
        assert age_band(person(date(2008, 3, 10))) == AgeBand.ADULT
        assert age_band(person(date(2008, 3, 11))) == AgeBand.MINOR


def test_labels_never_reveal_the_date():
    assert [str(b.label) for b in AgeBand] == ["Major d'edat", "Menor d'edat", "Edat desconeguda"]
