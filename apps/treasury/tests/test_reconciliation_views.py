"""Pantalla de conciliació (T-M04-15, segon tall; C5 i C6; P-M04-E, passos 3 i 5; M04-4: T1 per
veure-la, T4 per confirmar, desfer i excloure). Només dades inventades."""

import pytest
from django.urls import reverse

from apps.core import audit, charges
from apps.core.models import Charge, Person, Role, RolePermission
from apps.core.tests.conftest import (
    main_of,
    make_admin,  # noqa: F401 (fixture)
)
from apps.treasury import reconciliation
from apps.treasury.models import Reconciliation, ReconciliationUndo, StatementLineState
from apps.treasury.references import transfer_reference
from apps.treasury.tests.test_reconciliation import lines
from apps.treasury.tests.test_views import MANAGEMENT_ROLES, WITH_T1, client_for

pytestmark = pytest.mark.django_db
R = Role.Code
PAGE = reverse("administration:treasury_reconciliation")
REASON = "Casada amb el càrrec equivocat (prova)"


@pytest.fixture
def quota():
    person = Person.objects.create(first_name="Marta", last_name="Prova Inventada", origin="web")
    return charges.create_charge(
        person, kind="fee", amount_cents=9000, concept="Quota 2026", origin="proves",
        by=audit.system("proves"),
    )  # fmt: skip


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin(R.TREASURER)


def proposed(by, charge):
    (line,) = lines(by, (9000, f"TRANSF {transfer_reference(charge)} M INVENTADA"))
    return line


def confirm_url(line):
    return reverse("administration:treasury_confirm_line", args=[line.pk])


def undo_url(done):
    return reverse("administration:treasury_undo_reconciliation", args=[done.pk])


@pytest.mark.parametrize("role", MANAGEMENT_ROLES)
def test_t1_cell_of_each_role(make_admin, role):  # noqa: F811
    assert client_for(make_admin(role)).get(PAGE).status_code == (200 if role in WITH_T1 else 404)


def test_the_treasurer_sees_the_line_and_the_proposal(treasurer, quota):
    proposed(treasurer, quota)
    html = main_of(client_for(treasurer).get(PAGE).content.decode())
    # M04-4: el concepte de la línia només surt aquí; del càrrec, nom, concepte i import.
    assert "M INVENTADA" in html and "Marta Prova Inventada" in html and "Quota 2026" in html
    assert "Proposada" in html and ">Confirma</button>" in html


def test_without_t4_there_is_no_action_and_the_post_is_not_found(make_admin, treasurer, quota):  # noqa: F811
    line = proposed(treasurer, quota)
    admin = client_for(make_admin(R.ADMINISTRATOR))  # T1 sí, T4 no (P-112)
    html = main_of(admin.get(PAGE).content.decode())
    assert "Proposada" in html and ">Confirma</button>" not in html
    assert admin.post(confirm_url(line)).status_code == 404
    assert client_for(make_admin(R.SECRETARY)).post(confirm_url(line)).status_code == 404
    quota.refresh_from_db()
    assert quota.status == Charge.Status.PENDING


def test_confirm_and_undo_are_post_with_csrf(treasurer, quota):
    line = proposed(treasurer, quota)
    client = client_for(treasurer)
    assert client.get(confirm_url(line)).status_code == 405
    client.handler.enforce_csrf_checks = True
    assert client.post(confirm_url(line)).status_code == 403
    assert not Reconciliation.objects.exists()


def test_confirm_then_undo_with_a_reason(treasurer, quota):
    line = proposed(treasurer, quota)
    client = client_for(treasurer)
    response = client.post(confirm_url(line), follow=True)
    assert "Conciliació confirmada" in response.content.decode()
    quota.refresh_from_db()
    assert quota.status == Charge.Status.PAID
    done = Reconciliation.objects.get()
    html = main_of(client.get(PAGE).content.decode())
    assert "Conciliada" in html and "Desfés" in html

    response = client.post(undo_url(done), {"motiu": "  "}, follow=True)
    assert "Per desfer una conciliació cal" in response.content.decode()
    assert not ReconciliationUndo.objects.exists()

    response = client.post(undo_url(done), {"motiu": REASON}, follow=True)
    assert "Conciliació desfeta" in response.content.decode()
    quota.refresh_from_db()
    assert quota.status == Charge.Status.PENDING
    assert ReconciliationUndo.objects.get().reason == REASON


def test_a_rejected_confirmation_shows_the_reason(treasurer, quota):
    (line,) = lines(treasurer, (4200, "TRANSF SENSE REFERENCIA"))
    response = client_for(treasurer).post(confirm_url(line), follow=True)
    assert "no té cap proposta" in response.content.decode()


def test_exclude_from_this_screen_comes_back_here(treasurer):
    (line,) = lines(treasurer, (4200, "INGRES DESCONEGUT"))
    url = reverse("administration:treasury_exclude_line", args=[line.pk])
    response = client_for(treasurer).post(url, {"motiu": "No és del club", "des_de": "conciliacio"})
    assert response["Location"] == PAGE
    reconciliation.refresh()
    assert StatementLineState.objects.get(statement_line=line).status == "excluded"


def test_without_t8_or_t10_the_screen_does_not_link_them(treasurer):
    # P-190 (095): l'enllaç a la llista «a revisar» demana T10, i el botó «Exclou…», T8. Amagar-los
    # no és el control: la vista i el servei tornen a comprovar el permís.
    lines(treasurer, (4200, "INGRES DESCONEGUT"))
    client = client_for(treasurer)
    html = main_of(client.get(PAGE).content.decode())
    assert "Mira les línies a revisar" in html and "Exclou…" in html
    RolePermission.objects.filter(
        permission_code__in=(reconciliation.EXCLUDE, reconciliation.REVIEW)
    ).delete()
    html = main_of(client.get(PAGE).content.decode())
    assert "Mira les línies a revisar" not in html and "Exclou…" not in html
