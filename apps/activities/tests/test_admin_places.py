"""Apartat «Llocs» dels ajustos del 02 a l'administració (T-M02-39; AC21 i AC22; RN-M02-38, 39 i
46; CA-M02-41, 42, 44 i 46). Els serveis ja tenen les seves proves a `test_places.py`; aquí, les
pantalles i els permisos al servidor. Només dades inventades."""

import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.security import AREA_ADMIN
from apps.activities import catalogue
from apps.activities.models import Place, PlacePrice
from apps.activities.views.admin_places import EDIT_DENIED
from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.equipment.models import DiveCentre
from apps.equipment.places import usual_centre

from .helpers import an_outing

R = Role.Code
PLACES = reverse("administration:places")
ADD = reverse("administration:place_add")
ADD_OUTING = reverse("administration:activity_outing_add")


def detail(place):
    return reverse("administration:place_detail", args=[place.pk])


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(R.COURSES_MANAGER)


@pytest.fixture
def client_of(login_as):
    return lambda account: login_as(account, AREA_ADMIN)


@pytest.fixture
def place(manager):
    return catalogue.create_place(by=manager, name="Cala de pantalla", notes="Aparcar a dalt.")


@pytest.mark.parametrize("role", [R.INSTRUCTOR, R.SECRETARY, R.BOARD])
def test_without_ac21_everything_is_not_found(client_of, make_admin, place, role):  # noqa: F811
    client = client_of(make_admin(role))
    for url in (PLACES, ADD, detail(place)):
        assert client.get(url).status_code == 404, url
    assert client.post(detail(place), {"actiu": "0"}).status_code == 404
    assert Place.objects.get().active


def test_ca_m02_46_ac21_without_ac22_reads_and_cannot_edit(client_of, make_admin, place):  # noqa: F811
    keeper = make_admin(R.EQUIPMENT_MANAGER)  # AC21 sense AC22
    client = client_of(keeper)
    listing = main_of(client.get(PLACES).content.decode())
    assert "Cala de pantalla" in listing and ADD not in listing
    page = main_of(client.get(detail(place)).content.decode())
    assert "Aparcar a dalt." in page and "<form" not in page
    assert client.get(ADD).status_code == 404
    response = client.post(detail(place), {"desa_lloc": "1", "name": "Canviat", "notes": ""})
    assert response.status_code == 404
    place.refresh_from_db()
    assert place.name == "Cala de pantalla"
    denied = AuditEntry.objects.filter(action=EDIT_DENIED)
    assert denied.count() == 1 and denied.get().actor_account_id == keeper.pk


def test_ca_m02_42_a_new_place_is_in_the_selector_at_once(client_of, manager):
    client = client_of(manager)
    response = client.post(ADD, {"name": "Lloc de prova", "notes": ""})
    new = Place.objects.get(name="Lloc de prova")
    assert response.status_code == 303 and response["Location"] == detail(new)
    assert AuditEntry.objects.filter(action=catalogue.PLACE_CREATED).count() == 1
    assert "Lloc de prova" in client.get(ADD_OUTING).content.decode()


def test_a_repeated_name_stays_on_the_form(client_of, manager, place):
    response = client_of(manager).post(ADD, {"name": "cala de pantalla", "notes": ""})
    assert response.status_code == 200 and Place.objects.count() == 1
    assert "Ja hi ha un lloc amb aquest nom." in response.content.decode()


def test_ca_m02_41_deactivated_place_leaves_the_selector_not_deleted(client_of, manager, place):
    activity = an_outing(manager, place=place, price_member_cents=0, price_non_member_cents=0)
    client = client_of(manager)
    page = main_of(client.get(detail(place)).content.decode())
    assert "Esborra" not in page
    assert client.post(detail(place), {"actiu": "0"}).status_code == 303
    place.refresh_from_db()
    assert not place.active
    assert "Cala de pantalla" not in client.get(ADD_OUTING).content.decode()
    activity_page = client.get(reverse("administration:activity_detail", args=[activity.pk]))
    assert "Cala de pantalla" in activity_page.content.decode()


def test_ca_m02_44_a_price_from_tomorrow_and_a_past_date_rejected(client_of, manager, place):
    client = client_of(manager)
    tomorrow = timezone.localdate() + datetime.timedelta(days=1)
    price = {"nou_preu": "1", "price_member_cents": "50", "price_non_member_cents": "65"}
    past = {**price, "valid_from": "2020-01-01", "note": "Barca més cara."}
    response = client.post(detail(place), past)
    assert response.status_code == 200 and not PlacePrice.objects.exists()
    response = client.post(detail(place), {**price, "valid_from": tomorrow.isoformat()})
    assert response.status_code == 200 and not PlacePrice.objects.exists()  # sense motiu
    response = client.post(
        detail(place), {**price, "valid_from": tomorrow.isoformat(), "note": "Barca més cara."}
    )
    assert response.status_code == 303
    version = PlacePrice.objects.get()
    assert (version.price_member_cents, version.valid_from) == (5000, tomorrow)
    page = main_of(client.get(detail(place)).content.decode())
    assert "Sense preu" in page and "Futur" in page and "Barca més cara." in page


def test_editing_saves_the_previous_value_and_the_usual_centre(client_of, manager, place):
    centre = DiveCentre.objects.create(name="Centre inventat")
    field = "equipment_usual_centre__usual_centre"
    data = {"desa_lloc": "1", "name": "Cala nova", "notes": "", field: centre.pk}
    assert client_of(manager).post(detail(place), data).status_code == 303
    place.refresh_from_db()
    assert place.name == "Cala nova" and usual_centre(place) == centre
    entry = AuditEntry.objects.get(action=catalogue.PLACE_UPDATED, field="name")
    assert entry.old_value == "Cala de pantalla"
