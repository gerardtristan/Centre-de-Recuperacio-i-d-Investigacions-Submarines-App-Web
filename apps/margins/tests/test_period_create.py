"""T-M09-16c: crear el període següent (RN-M09-28; CA-M09-35, a nivell de servei) i la pantalla
dels períodes (P-M09-G; MG11 i MG12). Només dades inventades."""

import datetime

import pytest
from django.http import Http404
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.core import business_settings
from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.margins import period_closing
from apps.margins.models import Period
from apps.margins.tests.test_period_closing import NOV, an_expense, period

pytestmark = pytest.mark.django_db
R = Role.Code
D = datetime.date
TODAY = D(2027, 4, 15)
PAGE = reverse("administration:margin_periods")


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin(R.TREASURER)


def dates():
    return list(Period.objects.order_by("starts_on").values_list("starts_on", "ends_on"))


def test_el_primer_periode_comenca_el_dia_que_es_tria_i_dura_un_mes(treasurer):
    assert business_settings.get(period_closing.LENGTH) == "monthly"  # VC-32, d'inici
    with pytest.raises(period_closing.ValidationError):
        period_closing.create_next(by=treasurer, today=TODAY)
    period_closing.create_next(by=treasurer, starts_on=D(2027, 1, 1), today=TODAY)
    period_closing.create_next(by=treasurer, starts_on=D(2030, 1, 1), today=TODAY)  # s'ignora
    assert dates() == [(D(2027, 1, 1), D(2027, 1, 31)), (D(2027, 2, 1), D(2027, 2, 28))]
    entry = AuditEntry.objects.filter(action=period_closing.PERIOD_CREATED).last()
    assert entry.details["length"] == "monthly" and entry.actor_account == treasurer


def test_ca_m09_35_la_durada_nova_nomes_val_per_als_periodes_nous(treasurer, monkeypatch):
    period((D(2027, 2, 1), D(2027, 2, 28)))
    period((D(2027, 3, 1), D(2027, 3, 31)))
    monkeypatch.setattr(period_closing.business_settings, "get", lambda key, at=None: "quarterly")
    period_closing.create_next(by=treasurer, today=TODAY)
    assert dates() == [
        (D(2027, 2, 1), D(2027, 2, 28)),
        (D(2027, 3, 1), D(2027, 3, 31)),
        (D(2027, 4, 1), D(2027, 6, 30)),
    ]


def test_no_s_apilen_periodes_futurs(treasurer):
    period((D(2027, 5, 1), D(2027, 5, 31)))
    with pytest.raises(period_closing.ValidationError):
        period_closing.create_next(by=treasurer, today=TODAY)


@pytest.mark.parametrize(
    ("start", "months", "end"),
    [(D(2027, 1, 31), 1, D(2027, 2, 28)), (D(2027, 11, 1), 3, D(2028, 2, 1))],
)
def test_sumar_mesos(start, months, end):
    assert period_closing._add_months(start, months) == end


def test_sense_mg11_no_es_crea(make_admin):  # noqa: F811
    with pytest.raises(Http404):
        period_closing.create_next(by=make_admin(R.SECRETARY), starts_on=D(2027, 1, 1))


def test_la_pantalla_tanca_amb_un_motiu_per_element(login_as, treasurer):
    november = period(NOV)
    spent = an_expense(treasurer, D(2026, 11, 10))
    client = login_as(treasurer, AREA_ADMIN)
    html = main_of(client.get(PAGE).content.decode())
    assert "Tancar el període del 01/11/2026 al 30/11/2026" in html
    assert "Despesa sense factura: Sortida a les Medes." in html and "Reobre" not in html
    close = reverse("administration:margin_period_close", args=[november.pk])
    html = client.post(close, follow=True).content.decode()
    assert "Encara no es pot tancar" in html
    field = f"motiu-expense_without_invoice:{spent.pk}"
    html = client.post(close, {field: "La factura arriba el mes vinent"}, follow=True)
    assert "Període tancat." in html.content.decode()
    november.refresh_from_db()
    assert november.status == Period.Status.CLOSED


def test_la_pantalla_crea_el_primer_periode(login_as, treasurer):
    client = login_as(treasurer, AREA_ADMIN)
    assert "Encara no hi ha cap període." in main_of(client.get(PAGE).content.decode())
    create = reverse("administration:margin_period_create")
    response = client.post(create, {"starts_on": "2026-11-01"}, follow=True)
    assert "Període creat: del 01/11/2026 al 30/11/2026." in response.content.decode()


def test_nomes_l_administracio_reobre(login_as, treasurer, make_admin):  # noqa: F811
    november = period(NOV)
    period_closing.close(november, by=treasurer)
    reopen = reverse("administration:margin_period_reopen", args=[november.pk])
    assert login_as(treasurer, AREA_ADMIN).post(reopen, {"reason": "x"}).status_code == 404
    client = login_as(make_admin(R.ADMINISTRATOR), AREA_ADMIN)
    assert "Reobrir el període del 01/11/2026 al 30/11/2026" in client.get(PAGE).content.decode()
    assert "Cal el motiu" in client.post(reopen, {"reason": " "}, follow=True).content.decode()
    response = client.post(reopen, {"reason": "Repartiment mal fet (inventat)."}, follow=True)
    assert "Període reobert." in response.content.decode()


def test_sense_mg11_la_pantalla_no_es_troba(login_as, make_admin):  # noqa: F811
    assert login_as(make_admin(R.SECRETARY), AREA_ADMIN).get(PAGE).status_code == 404
