"""Catàlegs de cursos i d'especialitats a l'administració (T-M02-05b; AC6; RN-M02-01 i 05;
CA-M02-01 i 26). Els serveis ja tenen les seves proves a `test_catalogue.py`; aquí, les pantalles
i el permís al servidor. Només dades inventades."""

import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.security import AREA_ADMIN
from apps.activities import catalogue
from apps.activities.models import (
    EnvironmentalProject,
    EnvironmentalSubtype,
    OutingType,
    TrainingCatalogueEntry,
    TrainingCataloguePrice,
)
from apps.core.models import AuditEntry, Role, RolePermission
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)

from .helpers import a_course, an_entry, general

R = Role.Code
LIST = reverse("administration:catalogue")
ADD = reverse("administration:catalogue_entry_add")


def detail(entry):
    return reverse("administration:catalogue_entry", args=[entry.pk])


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(R.COURSES_MANAGER)


@pytest.fixture
def client_of(login_as):
    return lambda account: login_as(account, AREA_ADMIN)


@pytest.mark.parametrize("role", [R.INSTRUCTOR, R.SECRETARY, R.EQUIPMENT_MANAGER, R.BOARD])
def test_without_ac6_everything_is_not_found(client_of, make_admin, manager, role):  # noqa: F811
    entry = an_entry(manager)
    client = client_of(make_admin(role))
    for url in (LIST, ADD, detail(entry)):
        assert client.get(url).status_code == 404, url
    assert client.post(detail(entry), {"activa": "0"}).status_code == 404
    assert TrainingCatalogueEntry.objects.get().active


def test_a_new_entry_with_prices_in_euros(client_of, manager):
    data = {
        "kind": "course", "name": "Curs de pantalla", "default_places": "6",
        "price_member_cents": "45", "price_non_member_cents": "60,50",
        "department": general().pk,
    }  # fmt: skip
    response = client_of(manager).post(ADD, data)
    entry = TrainingCatalogueEntry.objects.get()
    assert response.status_code == 303 and response["Location"] == detail(entry)
    assert (entry.price_member_cents, entry.price_non_member_cents) == (4500, 6050)
    assert AuditEntry.objects.filter(action=catalogue.ENTRY_CREATED).count() == 1


def test_ca_m02_01_and_26_a_new_price_leaves_created_activities(client_of, manager):
    entry = an_entry(manager)
    course = a_course(manager, entry)
    tomorrow = timezone.localdate() + datetime.timedelta(days=1)
    prices = {"nou_preu": "1", "price_member_cents": "50", "price_non_member_cents": "65"}
    client = client_of(manager)
    response = client.post(detail(entry), {**prices, "valid_from": tomorrow.isoformat()})
    assert response.status_code == 200  # sense motiu
    data = {**prices, "valid_from": tomorrow.isoformat(), "note": "Pujada inventada."}
    assert client.post(detail(entry), data).status_code == 303
    version = TrainingCataloguePrice.objects.get(valid_from=tomorrow)
    assert version.price_member_cents == 5000
    course.refresh_from_db()
    assert course.price_member_cents == 4500
    assert AuditEntry.objects.filter(action=catalogue.PRICE_CHANGED).exists()
    page = main_of(client.get(detail(entry)).content.decode())
    assert "Futur" in page and "Pujada inventada." in page


def test_editing_keeps_the_previous_value_and_deactivating_hides_it(client_of, manager):
    entry = an_entry(manager, name="Abans")
    client = client_of(manager)
    form = client.get(detail(entry)).context["entry_form"]
    data = {n: form[n].value() for n in form.fields if form[n].value() not in (None, False)}
    response = client.post(detail(entry), {**data, "desa_fitxa": "1", "name": "Després"})
    assert response.status_code == 303
    entry.refresh_from_db()
    assert entry.name == "Després" and entry.price_member_cents == 4500
    change = AuditEntry.objects.get(action=catalogue.ENTRY_UPDATED, field="name")
    assert change.old_value == "Abans"
    assert client.post(detail(entry), {"activa": "0"}).status_code == 303
    entry.refresh_from_db()
    assert not entry.active
    add_course = client.get(reverse("administration:activity_course_add")).content.decode()
    assert "Després" not in add_course


def test_t_m02_05c_types_subtypes_and_projects_on_the_catalogue_page(client_of, manager):
    client = client_of(manager)
    data = {
        "nou_tipus": "1",
        "tipus-name": "Tipus inventat",
        "tipus-default_department": general().pk,
    }
    assert client.post(LIST, data).status_code == 303
    new = OutingType.objects.get(name="Tipus inventat")
    assert client.post(LIST, {"id": new.pk, "mode": "block"}).status_code == 303
    assert client.post(LIST, {"classe": "tipus", "id": new.pk, "actiu": "0"}).status_code == 303
    new.refresh_from_db()
    assert (new.default_requirements_mode, new.active) == ("block", False)
    assert (
        "Tipus inventat"
        not in client.get(reverse("administration:activity_outing_add")).content.decode()
    )
    assert (
        client.post(LIST, {"nou_subtipus": "1", "subtipus-name": "Subtipus inventat"}).status_code
        == 303
    )
    assert EnvironmentalSubtype.objects.filter(name="Subtipus inventat").exists()
    project = {
        "nou_projecte": "1",
        "projecte-name": "Projecte inventat",
        "projecte-department": general().pk,
    }
    response = client.post(LIST, project)  # sense objectiu
    assert response.status_code == 200 and not EnvironmentalProject.objects.exists()
    assert (
        client.post(LIST, {**project, "projecte-objective": "Comptar nacres."}).status_code == 303
    )
    assert EnvironmentalProject.objects.get().objective == "Comptar nacres."


def test_t_m02_05c_without_ac6_nothing_changes(client_of, make_admin):  # noqa: F811
    outing_type = OutingType.objects.first()
    client = client_of(make_admin(R.EQUIPMENT_MANAGER))
    response = client.post(LIST, {"classe": "tipus", "id": outing_type.pk, "actiu": "0"})
    assert response.status_code == 404
    outing_type.refresh_from_db()
    assert outing_type.active


FIELD = "El preu inclou la primera llicència de l'alumne"


def test_t_m02_50b_ac28_sees_the_field_with_the_proposal_and_saves_it(client_of, manager):
    entry = an_entry(manager)
    client = client_of(manager)
    form = client.get(detail(entry)).context["price_form"]
    assert form.fields["includes_first_licence"].initial is False
    star = catalogue.create_level(by=manager, name="Una estrella (inventat)", rank=20)
    TrainingCatalogueEntry.objects.filter(pk=entry.pk).update(official_level=star)
    form = client.get(detail(entry)).context["price_form"]
    assert form.fields["includes_first_licence"].initial is True
    tomorrow = (timezone.localdate() + datetime.timedelta(days=1)).isoformat()
    data = {
        "nou_preu": "1", "price_member_cents": "45", "price_non_member_cents": "60",
        "valid_from": tomorrow, "note": "Inclou la llicència (inventat).",
        "includes_first_licence": "on",
    }  # fmt: skip
    assert client.post(detail(entry), data).status_code == 303
    assert TrainingCataloguePrice.objects.get(valid_from=tomorrow).includes_first_licence


def test_t_m02_50b_without_ac28_no_field_and_the_value_is_kept(client_of, make_admin, manager):  # noqa: F811
    entry = an_entry(manager)
    catalogue.change_prices(
        entry, by=manager, price_member_cents=4500, price_non_member_cents=6000,
        valid_from=timezone.localdate(), note="Inclosa (inventat).", includes_first_licence=True,
    )  # fmt: skip
    RolePermission.objects.filter(
        role__code=R.COURSES_MANAGER, permission_code="activities.first_licence.manage"
    ).delete()
    client = client_of(make_admin(R.COURSES_MANAGER))
    page = main_of(client.get(detail(entry)).content.decode())
    assert FIELD not in page and "Inclou la primera llicència" in page  # AC27: el veu
    tomorrow = (timezone.localdate() + datetime.timedelta(days=1)).isoformat()
    data = {
        "nou_preu": "1", "price_member_cents": "50", "price_non_member_cents": "60",
        "valid_from": tomorrow, "note": "Pujada (inventat).", "includes_first_licence": "",
    }  # fmt: skip
    assert client.post(detail(entry), data).status_code == 303
    assert TrainingCataloguePrice.objects.get(valid_from=tomorrow).includes_first_licence
    RolePermission.objects.filter(
        role__code=R.COURSES_MANAGER, permission_code="activities.first_licence.view"
    ).delete()
    page = main_of(client_of(make_admin(R.COURSES_MANAGER)).get(detail(entry)).content.decode())
    assert "primera llicència" not in page
