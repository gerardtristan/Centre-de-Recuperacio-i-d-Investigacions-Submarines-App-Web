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
from apps.treasury.references import check_character, transfer_reference
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


# --- P-190 (095): T8 (excloure) i T10 (la llista «a revisar») van per separat de T4 i T1. Amagar
# un enllaç no és el control: la vista i el servei tornen a comprovar el permís.
T1, T4 = "treasury.view", reconciliation.RECONCILE
T8, T10 = reconciliation.EXCLUDE, reconciliation.REVIEW
REVIEW = reverse("administration:treasury_review")
HOME = reverse("administration:home")


def grant(role, *codes):
    for code in codes:
        RolePermission.objects.get_or_create(
            role=Role.objects.get(code=role), permission_code=code, defaults={"scope": "all"}
        )


def revoke(role, *codes):
    RolePermission.objects.filter(role__code=role, permission_code__in=codes).delete()


def html_of(client, url):
    response = client.get(url)
    assert response.status_code == 200
    return main_of(response.content.decode())


@pytest.fixture
def to_review(treasurer, settings):
    """Una línia d'entrada «a revisar»: referència vàlida, però de cap càrrec."""
    settings.TRANSFER_REFERENCE_PREFIX = "CRIS"
    (line,) = lines(treasurer, (777, f"CRIS-AB2CD-{check_character('AB2CD')} JOAN INVENTAT"))
    return line


def test_without_t10_the_screen_still_offers_exclude_but_not_the_list(treasurer):
    lines(treasurer, (4200, "INGRES DESCONEGUT"))
    revoke(R.TREASURER, T10)
    html = html_of(client_for(treasurer), PAGE)
    assert "Exclou…" in html and "Mira les línies a revisar" not in html


def test_without_t8_the_screen_still_links_the_list_but_not_exclude(treasurer):
    lines(treasurer, (4200, "INGRES DESCONEGUT"))
    revoke(R.TREASURER, T8)
    html = html_of(client_for(treasurer), PAGE)
    assert "Mira les línies a revisar" in html and "Exclou…" not in html
    assert "Casa a mà…" in html  # T4, que encara té


def test_t8_without_t4_only_offers_exclude_on_the_reconciliation_screen(make_admin, treasurer):  # noqa: F811
    lines(treasurer, (4200, "INGRES DESCONEGUT"))
    grant(R.SECRETARY, T1, T8)
    html = html_of(client_for(make_admin(R.SECRETARY)), PAGE)
    assert "Exclou…" in html
    assert "Casa a mà…" not in html and "Mira les línies a revisar" not in html


def test_on_the_list_match_needs_t4_and_exclude_needs_t8(make_admin, treasurer, to_review):  # noqa: F811
    match = reverse("administration:treasury_match_line", args=[to_review.pk])
    revoke(R.TREASURER, T4)
    html = html_of(client_for(treasurer), REVIEW)
    assert "Exclou…" in html and match not in html
    grant(R.SECRETARY, T4, T10)
    html = html_of(client_for(make_admin(R.SECRETARY)), REVIEW)
    assert match in html and "Exclou…" not in html


def test_after_excluding_without_t10_it_goes_back_to_reconciliation(make_admin, treasurer):  # noqa: F811
    first, second = lines(treasurer, (4200, "INGRES DESCONEGUT"), (-500, "REBUT AIGUA"))
    grant(R.SECRETARY, T1, T8)
    secretary = client_for(make_admin(R.SECRETARY))
    url = reverse("administration:treasury_exclude_line", args=[first.pk])
    assert secretary.post(url, {"motiu": "No és del club"})["Location"] == PAGE
    revoke(R.SECRETARY, T1)  # ni la llista ni la conciliació: a l'inici
    url = reverse("administration:treasury_exclude_line", args=[second.pk])
    assert secretary.post(url, {"motiu": "No és del club"})["Location"] == HOME


def test_the_back_link_of_the_list_only_if_its_screen_opens(make_admin, treasurer):  # noqa: F811
    accounts = reverse("administration:treasury_accounts")
    assert accounts in html_of(client_for(treasurer), REVIEW)
    grant(R.SECRETARY, T10)
    html = html_of(client_for(make_admin(R.SECRETARY)), REVIEW)
    assert accounts not in html and f'href="{HOME}"' in html


# --- T-M04-14d (097, P-192 opció C; RN-T15): excloure una línia proposada i desfer una exclusió,
# totes dues amb T8 i motiu, des de la conciliació.


def undo_exclusion_url(line):
    return reverse("administration:treasury_undo_exclusion", args=[line.pk])


def test_a_proposed_line_offers_confirm_and_exclude(treasurer, quota):
    line = proposed(treasurer, quota)
    html = html_of(client_for(treasurer), PAGE)
    exclude = reverse("administration:treasury_exclude_line", args=[line.pk])
    assert ">Confirma</button>" in html and exclude in html


def test_an_excluded_line_offers_undo_only_with_t8(make_admin, treasurer):  # noqa: F811
    (line,) = lines(treasurer, (4200, "INGRES DESCONEGUT"))
    reconciliation.exclude(line, reason="No és del club", by=treasurer)
    html = html_of(client_for(treasurer), PAGE)
    assert "Desfés l'exclusió…" in html and undo_exclusion_url(line) in html
    admin = client_for(make_admin(R.ADMINISTRATOR))  # T1 sí, T8 no
    assert undo_exclusion_url(line) not in html_of(admin, PAGE)
    assert admin.post(undo_exclusion_url(line), {"motiu": "Prova"}).status_code == 404
    assert StatementLineState.objects.get(statement_line=line).status == "excluded"


def test_undoing_an_exclusion_from_the_screen(treasurer, quota):
    line = proposed(treasurer, quota)
    reconciliation.exclude(line, reason="Repetit", by=treasurer)
    client = client_for(treasurer)
    assert client.get(undo_exclusion_url(line)).status_code == 405
    response = client.post(undo_exclusion_url(line), {"motiu": ""}, follow=True)
    assert "Per desfer l&#x27;exclusió cal escriure&#x27;n el motiu." in response.content.decode()
    response = client.post(undo_exclusion_url(line), {"motiu": "Era bona"})
    assert response["Location"] == PAGE
    html = html_of(client, PAGE)
    assert "Exclusió desfeta." in html and ">Confirma</button>" in html  # torna a ser proposada
    missing = reverse("administration:treasury_undo_exclusion", args=[999999])
    assert client.post(missing, {"motiu": "x"}).status_code == 404
