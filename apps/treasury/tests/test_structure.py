"""Departaments, centres de cost i comptes (T-M04-22; P-410 i P-411, decisió 105; VC-08):
crear, reanomenar i desactivar amb registre; les entrades del sistema protegides al servidor.
Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse

from apps.core import charges
from apps.core.models import AuditEntry, Department, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client
from apps.treasury import structure
from apps.treasury.models import CostCentre, TreasuryAccount

pytestmark = pytest.mark.django_db
R = Role.Code
PAGE = reverse("administration:treasury_structure")


def edit_url(kind, pk):
    return reverse("administration:treasury_structure_edit", args=[kind, pk])


def create_url(kind):
    return reverse("administration:treasury_structure_create", args=[kind])


@pytest.fixture
def admin(make_admin):  # noqa: F811
    return make_admin(R.ADMINISTRATOR)


@pytest.fixture
def general():
    return Department.objects.get(name=Department.GENERAL)


def system_centres(general):
    return [CostCentre.objects.get(department=general, name=n) for n in
            ("Quotes de socis", "Ajustos de caixa")]  # fmt: skip


# --- Serveis -----------------------------------------------------------------------------------


def test_p410_a_department_is_renamed_with_the_previous_value(admin):
    department = charges.create_department("Medi ambient (inventat)", by=admin)
    charges.rename_department(department, " Medi marí ", by=admin)
    department.refresh_from_db()
    assert department.name == "Medi marí"
    entry = AuditEntry.objects.get(action="departments.renamed")
    assert (entry.old_value, entry.new_value) == ("Medi ambient (inventat)", "Medi marí")


def test_p411_general_is_neither_renamed_nor_deactivated(admin, general):
    for action in (lambda: charges.rename_department(general, "Altres", by=admin),
                   lambda: charges.deactivate_department(general, by=admin)):  # fmt: skip
        with pytest.raises(ValidationError):
            action()
    general.refresh_from_db()
    assert (general.name, general.active) == (Department.GENERAL, True)


def test_p410_cost_centres_are_created_renamed_and_deactivated_with_audit(admin, general):
    centre = structure.create_cost_centre(general, " Excursions ", by=admin)
    structure.rename_cost_centre(centre, "Sortides", by=admin)
    structure.deactivate_cost_centre(centre, by=admin)
    structure.deactivate_cost_centre(centre, by=admin)  # dues vegades: res més
    centre.refresh_from_db()
    assert (centre.name, centre.active) == ("Sortides", False)
    actions = list(AuditEntry.objects.filter(action__startswith="treasury.cost_centre_")
                   .order_by("pk").values_list("action", flat=True))  # fmt: skip
    assert actions == ["treasury.cost_centre_created", "treasury.cost_centre_renamed",
                       "treasury.cost_centre_deactivated"]  # fmt: skip


def test_p411_system_cost_centres_are_protected(admin, general):
    for centre in system_centres(general):
        with pytest.raises(ValidationError):
            structure.rename_cost_centre(centre, "Altres", by=admin)
        with pytest.raises(ValidationError):
            structure.deactivate_cost_centre(centre, by=admin)
        refreshed = CostCentre.objects.get(pk=centre.pk)
        assert (refreshed.name, refreshed.active) == (centre.name, True)


def test_an_inactive_department_takes_no_new_cost_centre_and_names_are_unique(admin, general):
    with pytest.raises(ValidationError):
        structure.create_cost_centre(general, "Quotes de socis", by=admin)
    department = charges.create_department("Història (inventat)", by=admin)
    charges.deactivate_department(department, by=admin)
    with pytest.raises(ValidationError):
        structure.create_cost_centre(department, "Conferències", by=admin)


@pytest.mark.parametrize("role", [R.TREASURER, R.ADMINISTRATOR])
def test_p410_accounts_are_created_renamed_and_deactivated(make_admin, role):  # noqa: F811
    by = make_admin(role)
    bank = structure.create_account("Banc inventat", "bank", last4="1234", by=by)
    cash = structure.create_account("Caixa de l'estand", "cash", by=by)
    structure.rename_account(bank, "Banc principal (inventat)", by=by)
    structure.deactivate_account(cash, by=by)
    bank.refresh_from_db()
    cash.refresh_from_db()
    assert (bank.name, bank.last4, cash.active) == ("Banc principal (inventat)", "1234", False)
    assert AuditEntry.objects.filter(action="treasury.account_renamed", old_value="Banc inventat",
                                     new_value="Banc principal (inventat)").exists()  # fmt: skip


@pytest.mark.parametrize(
    ("kind", "last4"), [("transit", None), ("bank", None), ("bank", "12AB"), ("cash", "1234")]
)
def test_an_invalid_account_is_rejected(admin, kind, last4):
    before = TreasuryAccount.objects.count()
    with pytest.raises(ValidationError):
        structure.create_account("Compte inventat", kind, last4=last4, by=admin)
    assert TreasuryAccount.objects.count() == before


@pytest.mark.parametrize("role", [R.SECRETARY, R.PRESIDENT, R.BOARD])
def test_without_the_permission_nothing_changes(make_admin, general, role):  # noqa: F811
    by = make_admin(role)
    for action in (lambda: charges.create_department("X", by=by),
                   lambda: structure.create_cost_centre(general, "X", by=by),
                   lambda: structure.create_account("X", "cash", by=by)):  # fmt: skip
        with pytest.raises(Http404):
            action()


def test_the_treasurer_does_not_manage_cost_centres_at_the_start(make_admin, general):  # noqa: F811
    # S-M04-09: T3 comença només amb l'administrador.
    with pytest.raises(Http404):
        structure.create_cost_centre(general, "X", by=make_admin(R.TREASURER))


# --- Pantalla ----------------------------------------------------------------------------------


def test_the_administrator_sees_everything_and_system_entries_have_no_action(admin, general):
    page = admin_client(admin).get(PAGE).content.decode()
    assert "Departaments i centres de cost" in page and "Comptes de tresoreria" in page
    assert "Entrada del sistema" in page and page.count("del sistema") >= 3
    assert edit_url("departament", general.pk) not in page
    for centre in system_centres(general):
        assert edit_url("centre", centre.pk) not in page
    llicencies = CostCentre.objects.get(department=general, name="Llicències")
    assert edit_url("centre", llicencies.pk) in page


def test_the_treasurer_only_sees_and_creates_accounts(make_admin):  # noqa: F811
    client = admin_client(make_admin(R.TREASURER))
    page = client.get(PAGE).content.decode()
    assert "Comptes de tresoreria" in page and "Departaments i centres de cost" not in page
    data = {"compte-name": "Caixa inventada", "compte-kind": "cash", "compte-last4": ""}
    assert client.post(create_url("compte"), data).status_code == 302
    assert TreasuryAccount.objects.filter(name="Caixa inventada", kind="cash").exists()
    assert client.post(create_url("centre"), {"centre-name": "X"}).status_code == 404


def test_a_bank_account_without_digits_shows_the_error_and_saves_nothing(admin):
    client = admin_client(admin)
    data = {"compte-name": "Banc inventat", "compte-kind": "bank", "compte-last4": ""}
    response = client.post(create_url("compte"), data)
    assert response.status_code == 200
    assert "quatre darrers dígits" in response.content.decode()
    assert not TreasuryAccount.objects.filter(name="Banc inventat").exists()


def test_rename_and_deactivate_from_the_screen(admin, general):
    client = admin_client(admin)
    centre = CostCentre.objects.get(department=general, name="Llicències")
    assert (
        client.post(edit_url("centre", centre.pk), {"name": "Llicències federatives"}).status_code
        == 302
    )
    assert client.post(edit_url("centre", centre.pk), {"desactiva": "1"}).status_code == 302
    centre.refresh_from_db()
    assert (centre.name, centre.active) == ("Llicències federatives", False)


@pytest.mark.parametrize("role", [R.SECRETARY, R.BOARD, R.INSTRUCTOR])
def test_without_any_permission_the_screen_is_not_found(make_admin, role):  # noqa: F811
    assert admin_client(make_admin(role)).get(PAGE).status_code == 404


def test_a_system_entry_or_an_unknown_kind_is_not_found(admin, general):
    client = admin_client(admin)
    assert client.get(edit_url("departament", general.pk)).status_code == 404
    for centre in system_centres(general):
        assert client.post(edit_url("centre", centre.pk), {"desactiva": "1"}).status_code == 404
    assert client.get(edit_url("altres", 1)).status_code == 404
