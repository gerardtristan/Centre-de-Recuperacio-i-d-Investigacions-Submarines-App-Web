"""Conciliació a l'escriptori (T-DX-72, PR 9b): el títol amb el que queda, els comptadors de
Deposito i el panell de la línia triada. El panell demana «Casa a mà», «Casa amb moviments» i
«Revisa i confirma» amb HTMX (`HX-Request`) a les mateixes vistes: mateix permís T4, mateix POST
amb CSRF i mateixes comprovacions d'estat; sense, la pàgina sencera, com abans. Només dades
inventades."""

import pytest
from django.urls import reverse

from apps.core.models import Charge, Role
from apps.core.tests.conftest import main_of
from apps.core.tests.conftest import make_admin as _make_admin
from apps.treasury import reconciliation
from apps.treasury.models import Reconciliation
from apps.treasury.tests import test_settlements as base
from apps.treasury.tests.test_reconciliation import charge as _charge
from apps.treasury.tests.test_reconciliation import lines, ref
from apps.treasury.tests.test_settlement_reconciliation import bank_line, received
from apps.treasury.tests.test_views import client_for

pytestmark = pytest.mark.django_db
make_admin, charge, person, transit = _make_admin, _charge, base.person, base.transit
treasurer, two = base.treasurer, base.two
HX = {"HX-Request": "true"}
PAGE = reverse("administration:treasury_reconciliation")


def match_url(line):
    return reverse("administration:treasury_match_line", args=[line.pk])


def movements_url(line):
    return reverse("administration:treasury_match_movements", args=[line.pk])


def settlement_url(line):
    return reverse("administration:treasury_confirm_settlement_line", args=[line.pk])


def test_the_title_says_what_is_left_and_the_counters_come_from_the_same_lines(treasurer, charge):
    quota = charge(9000)
    proposed, pending, done, out = lines(
        treasurer,
        (9000, f"TRANSF {ref(quota)}"),
        (4000, "TRANSF SENSE REFERENCIA"),
        (2500, "TRANSF ALTRA"),
        (-1000, "COMISSIO"),
    )
    reconciliation.refresh()
    reconciliation.exclude(out, reason="Comissió del banc (prova)", by=treasurer)
    reconciliation.exclude(done, reason="D'una altra entitat (prova)", by=treasurer)
    html = main_of(client_for(treasurer).get(PAGE).content.decode())
    assert "Queden 2 línies per conciliar" in html  # pendent + proposada
    assert '<li class="es-pendent"><b>1</b><span>pendent</span>' in html
    assert "<b>1</b><span>proposada</span>" in html
    assert "<b>0</b><span>conciliades</span>" in html
    assert "<b>2</b><span>excloses</span>" in html


def test_nothing_left_and_no_panel_without_lines(treasurer):
    html = main_of(client_for(treasurer).get(PAGE).content.decode())
    assert "No queda cap línia per conciliar" in html and "data-panell" not in html


def test_the_panel_and_its_links_only_with_t4(make_admin, treasurer, charge):
    (line,) = lines(treasurer, (4000, "TRANSF"))
    html = main_of(client_for(treasurer).get(PAGE).content.decode())
    assert "data-panell hidden" in html  # l'obre el JavaScript, mai el servidor
    assert f'href="{match_url(line)}" data-panell-enllac' in html
    html = main_of(client_for(make_admin(Role.Code.ADMINISTRATOR)).get(PAGE).content.decode())
    assert "data-panell" not in html  # T1 sense T4: ni el panell ni els enllaços


def test_match_for_the_panel_is_the_body_only_and_the_page_stays_whole(treasurer, charge):
    quota = charge(9000)
    (line,) = lines(treasurer, (9000, "TRANSF M INVENTADA"))
    client = client_for(treasurer)
    whole = client.get(match_url(line), {"cerca": ref(quota)}).content.decode()
    assert "<html" in whole and "<h1>Casa la línia a mà</h1>" in whole and "hx-get" not in whole
    part = client.get(match_url(line), {"cerca": ref(quota)}, headers=HX).content.decode()
    assert "<html" not in part and "barra-lateral" not in part
    assert "Torna a la conciliació" not in part
    assert '<h2 id="panell-linia-titol" tabindex="-1">Casa la línia a mà</h2>' in part
    assert "M INVENTADA" in part and f'value="{quota.pk}"' in part and "IBAN" not in part
    # La cerca i la revisió es queden al panell; la revisió és el POST de sempre, amb el CSRF
    assert f'hx-get="{match_url(line)}" hx-target="#panell-linia-cos"' in part
    assert f'hx-post="{match_url(line)}" hx-target="#panell-linia-cos"' in part
    assert 'name="csrfmiddlewaretoken"' in part
    review = client.post(match_url(line), {"carrec": quota.pk}, headers=HX).content.decode()
    assert "<html" not in review and "Confirma el casament" in review
    # La confirmació és un POST normal (sense hx-post): torna a la conciliació sencera
    assert review.count("hx-post") == 0 and 'name="confirma"' in review


def test_the_panel_needs_t4_and_the_csrf_like_the_page(make_admin, treasurer, charge):
    quota = charge(9000)
    (line,) = lines(treasurer, (9000, "TRANSF"))
    for role in (Role.Code.ADMINISTRATOR, Role.Code.SECRETARY):
        client = client_for(make_admin(role))
        assert client.get(match_url(line), headers=HX).status_code == 404
        assert client.get(movements_url(line), headers=HX).status_code == 404
        assert client.get(settlement_url(line), headers=HX).status_code == 404
    client = client_for(treasurer)
    client.handler.enforce_csrf_checks = True
    data = {"carrec": quota.pk, "confirma": "1"}
    assert client.post(match_url(line), data, headers=HX).status_code == 403
    quota.refresh_from_db()
    assert quota.status == Charge.Status.PENDING


def test_a_line_that_cannot_be_matched_says_so_in_the_panel_too(treasurer, charge):
    quota = charge(9000)
    (line,) = lines(treasurer, (9000, f"TRANSF {ref(quota)}"))
    reconciliation.confirm(line, by=treasurer)
    part = client_for(treasurer).get(match_url(line), headers=HX).content.decode()
    assert "no es pot casar" in part and 'name="cerca"' not in part


def test_a_failed_review_comes_back_to_the_panel_with_the_reason(treasurer, charge):
    quota = charge(9000)
    (line,) = lines(treasurer, (9500, "TRANSF"))
    reconciliation.refresh()
    client = client_for(treasurer)
    response = client.post(match_url(line), {"carrec": quota.pk}, headers=HX, follow=True)
    html = response.content.decode()
    assert "<html" not in html and "han de coincidir" in html


def test_movements_for_the_panel(treasurer):
    (line,) = lines(treasurer, (-4200, "REBUT LLUM"))
    part = client_for(treasurer).get(movements_url(line), headers=HX).content.decode()
    assert "<html" not in part and ">Casa la línia amb moviments</h2>" in part
    assert "Torna a la conciliació" not in part


def test_settlement_review_for_the_panel_and_cancel_closes_it(two, treasurer):
    settlement = received()
    line = bank_line(treasurer, concept="ABONAMENT M INVENTADA")
    client = client_for(treasurer)
    part = client.get(settlement_url(line), headers=HX).content.decode()
    assert "<html" not in part and ">Confirma la liquidació</h2>" in part
    assert "123,80" in part and "data-panell-tanca" in part and "hx-post" not in part
    whole = client.get(settlement_url(line)).content.decode()
    assert "<html" in whole and "data-panell-tanca" not in whole
    response = client.post(settlement_url(line), {"liquidacio": settlement.pk}, follow=True)
    assert "Liquidació conciliada" in response.content.decode()
    assert Reconciliation.objects.exists()


def test_a_panel_step_that_ends_on_the_reconciliation_loads_the_whole_page(two, treasurer):
    """Sense cap liquidació proposada, la vista torna a la conciliació: amb HTMX, HX-Redirect,
    perquè la conciliació no s'encasti dins del panell; el missatge surt a la pàgina."""
    line = bank_line(treasurer)  # cap liquidació rebuda: res proposat
    client = client_for(treasurer)
    response = client.get(settlement_url(line), headers=HX, follow=True)
    assert response.status_code == 204 and response["HX-Redirect"] == PAGE
    assert "no té cap liquidació proposada" in client.get(PAGE).content.decode()
