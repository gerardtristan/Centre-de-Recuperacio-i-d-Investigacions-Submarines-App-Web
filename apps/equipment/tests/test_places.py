"""T-M03-26: centre habitual del lloc i proposta de centre (RN-M03-23 i 24; CA-M03-23). Només
dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.activities.models import Place
from apps.core.models import AuditEntry
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment import places
from apps.equipment.models import DiveCentre, PlaceUsualCentre

pytestmark = pytest.mark.django_db


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin("courses_manager")  # AC22


@pytest.fixture
def place(manager):
    return Place.objects.create(name="Lloc de prova", created_by=manager)


@pytest.fixture
def centre_a():
    return DiveCentre.objects.create(name="Centre A")


def test_ca_m03_23_el_centre_proposat_es_l_habitual_si_es_actiu(place, centre_a, manager):
    row = places.set_usual_centre(place, centre_a, by=manager)
    assert (places.proposed_centre(place), str(row)) == (centre_a, f"{place.pk}: Centre A")
    assert places.usual_centre_inactive(place) is False

    DiveCentre.objects.filter(pk=centre_a.pk).update(active=False)
    assert places.proposed_centre(place) is None
    assert places.usual_centre_inactive(place) is True  # el lloc surt marcat


def test_canviar_i_treure_el_centre_habitual_queda_al_registre(place, centre_a, manager):
    centre_b = DiveCentre.objects.create(name="Centre B")
    places.set_usual_centre(place, centre_a, by=manager)
    places.set_usual_centre(place, centre_b, by=manager)
    assert PlaceUsualCentre.objects.get().centre == centre_b
    assert places.set_usual_centre(place, None, by=manager) is None
    assert places.set_usual_centre(place, None, by=manager) is None  # ja no en té
    assert not PlaceUsualCentre.objects.exists()
    values = list(
        AuditEntry.objects.filter(action=places.USUAL_CENTRE_CHANGED)
        .order_by("pk")
        .values_list("old_value", "new_value")
    )
    assert values == [
        (None, "Centre A"),
        ("Centre A", "Centre B"),
        ("Centre B", None),
        (None, None),
    ]


def test_nomes_un_centre_actiu_i_sense_lloc_no_es_proposa_res(place, manager):
    closed = DiveCentre.objects.create(name="Centre tancat", active=False)
    with pytest.raises(ValidationError):
        places.set_usual_centre(place, closed, by=manager)
    assert places.proposed_centre(None) is None
    assert places.proposed_centre(place) is None


@pytest.mark.parametrize("role", ["secretary", "board", "equipment_manager", None])
def test_sense_ac22_no_es_tria(place, centre_a, make_admin, role):  # noqa: F811
    with pytest.raises(Http404):
        places.set_usual_centre(place, centre_a, by=make_admin(*([role] if role else [])))
