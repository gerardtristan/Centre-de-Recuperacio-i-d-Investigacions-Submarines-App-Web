"""Pantalles d'administració del 02, T-M02-06b (i vistes de la T-M02-40): crear i editar un curs o
una sortida amb el lloc, el preu estàndard i el motiu (AC7, AC21; RN-M02-40 i 41; CA-M02-01 a 03 i
43). Només dades inventades."""

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.security import AREA_ADMIN
from apps.activities import catalogue, states
from apps.activities.models import Activity
from apps.core.models import Role, RolePermission
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)

from .helpers import an_entry, an_outing, entries_of, outing_type

R = Role.Code
ADD_OUTING = reverse("administration:activity_outing_add")
ADD_COURSE = reverse("administration:activity_course_add")


def edit_url(activity):
    return reverse("administration:activity_edit", args=[activity.pk])


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(R.COURSES_MANAGER)


@pytest.fixture
def client_of(login_as):
    return lambda account: login_as(account, AREA_ADMIN)


def a_place(manager, prices=(4500, 6000)):
    """Un lloc amb el preu estàndard vigent avui (el formulari i el servei miren el d'avui)."""
    place = catalogue.create_place(by=manager, name=f"Lloc de pantalla {manager.pk}-{prices}")
    if prices:
        catalogue.change_place_price(
            place, by=manager, price_member_cents=prices[0], price_non_member_cents=prices[1],
            valid_from=timezone.localdate(), note="Preu inicial inventat.",
        )  # fmt: skip
    return place


def outing_post(manager, place, **fields):
    data = {
        "outing_type": outing_type().pk,
        "title": "Sortida inventada a la pantalla",
        "starts_on": "2027-06-14",
        "ends_on": "2027-06-14",
        "place": place.pk,
        "registration_closes_at": "2027-06-10T20:00",
        "max_places": "12",
        "responsible": manager.person_id,
        **fields,
    }
    return {k: v for k, v in data.items() if v is not None}


@pytest.mark.parametrize("role", [R.INSTRUCTOR, R.SECRETARY, R.EQUIPMENT_MANAGER, R.BOARD])
def test_without_ac7_create_and_edit_are_not_found(client_of, make_admin, manager, role):  # noqa: F811
    activity = an_outing(manager)
    client = client_of(make_admin(role))
    for url in (ADD_OUTING, ADD_COURSE, edit_url(activity)):
        assert client.get(url).status_code == 404, url
    assert client.post(ADD_OUTING, outing_post(manager, a_place(manager))).status_code == 404
    assert Activity.objects.count() == 1


def test_outing_with_blank_prices_copies_the_place_standard(client_of, manager):
    response = client_of(manager).post(ADD_OUTING, outing_post(manager, a_place(manager)))
    activity = Activity.objects.get()
    assert response.status_code == 303
    assert response["Location"] == reverse("administration:activity_detail", args=[activity.pk])
    assert (activity.price_member_cents, activity.price_non_member_cents) == (4500, 6000)
    assert activity.standard_price_member_cents == 4500 and activity.status == "draft"


def test_place_without_standard_price_asks_for_both_prices(client_of, manager):
    place = a_place(manager, prices=None)
    client = client_of(manager)
    response = client.post(ADD_OUTING, outing_post(manager, place))
    assert response.status_code == 200 and not Activity.objects.exists()
    assert "Aquest lloc no té preu estàndard" in response.content.decode()
    response = client.post(
        ADD_OUTING,
        outing_post(manager, place, price_member_cents="40", price_non_member_cents="55,50"),
    )
    assert response.status_code == 303 and Activity.objects.get().price_non_member_cents == 5550


def test_price_different_from_the_standard_needs_a_note(client_of, manager):
    client = client_of(manager)
    different = outing_post(
        manager, a_place(manager), price_member_cents="50", price_non_member_cents="60"
    )
    response = client.post(ADD_OUTING, different)
    assert response.status_code == 200 and not Activity.objects.exists()
    assert "cal escriure" in response.content.decode()
    response = client.post(ADD_OUTING, {**different, "price_override_note": "Barca més cara."})
    assert response.status_code == 303
    assert Activity.objects.get().price_override_note == "Barca més cara."


def test_place_prices_in_the_selector_with_ac7_also_without_ac21(client_of, make_admin, manager):  # noqa: F811
    """RN-M02-46: el selector mostra el nom i el preu estàndard a qui té AC7, sense AC21."""
    a_place(manager)
    assert "estàndard: 45,00" in client_of(manager).get(ADD_OUTING).content.decode()
    RolePermission.objects.filter(
        role__code=R.COURSES_MANAGER, permission_code="activities.places.view"
    ).delete()
    other = make_admin(R.COURSES_MANAGER)
    assert "estàndard: 45,00" in client_of(other).get(ADD_OUTING).content.decode()


def test_course_copies_the_catalogue_entry(client_of, manager):
    entry = an_entry(manager, default_places=6)
    response = client_of(manager).post(
        ADD_COURSE,
        {
            "catalogue_entry": entry.pk,
            "title": "Curs inventat a la pantalla",
            "starts_on": "2027-06-14",
            "ends_on": "2027-06-15",
            "registration_closes_at": "2027-06-10T20:00",
            "responsible": manager.person_id,
        },
    )
    activity = Activity.objects.get()
    assert response.status_code == 303
    assert (activity.kind, activity.max_places, activity.place) == ("course", 6, None)
    assert activity.price_member_cents == 4500


def test_edit_saves_changes_with_the_previous_value_in_the_audit(client_of, manager):
    activity = an_outing(manager)
    client = client_of(manager)
    form = client.get(edit_url(activity)).context["form"]
    data = {n: form[n].value() for n in form.fields if form[n].value() not in (None, False, [])}
    data |= {"title": "Títol canviat", "registration_closes_at": "2027-06-10T20:00"}
    data |= {"price_member_cents": "45", "price_non_member_cents": "60"}
    response = client.post(edit_url(activity), data)
    assert response.status_code == 303
    activity.refresh_from_db()
    assert activity.title == "Títol canviat"
    assert entries_of(activity, "activities.activity.updated").filter(field="title").exists()


def test_cancelled_activity_has_no_edit_link_and_cannot_be_saved(client_of, manager):
    activity = an_outing(manager, title="Abans")
    states.cancel(activity, by=manager, reason="Mal temps inventat.")
    client = client_of(manager)
    detail = client.get(reverse("administration:activity_detail", args=[activity.pk]))
    assert edit_url(activity) not in main_of(detail.content.decode())
    response = client.post(edit_url(activity), {"title": "Després"})
    assert response.status_code == 200
    activity.refresh_from_db()
    assert activity.title == "Abans"
