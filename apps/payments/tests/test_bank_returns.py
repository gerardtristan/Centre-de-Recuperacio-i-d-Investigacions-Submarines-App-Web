"""Fitxer de retornats del banc en pain.002 (T-M05b-12b; banc fictici de la 092; P-M05b-F; B4).
Només dades inventades: el fitxer el fa la prova i cap referència no és real."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.urls import reverse

from apps.core import files
from apps.core.models import AuditEntry, Charge, Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.payments import bank_returns, returns
from apps.payments.models import DirectDebitItem
from apps.payments.tests.test_remittance_settlement import (  # noqa: F401 (fixtures)
    club,
    sent,
    sepa_balance,
    treasurer,
)
from apps.payments.tests.test_remittances import (  # noqa: F401 (fixtures)
    collection_date,
    signer,
    text,
)
from apps.payments.tests.test_returns import collected, settle  # noqa: F401 (fixture)
from apps.treasury.models import Movement
from apps.treasury.tests.test_views import client_for

pytestmark = pytest.mark.django_db
URL = reverse("administration:payments_returns")
FILE_URL = reverse("administration:payments_returns_file")
CONFIRM_URL = reverse("administration:payments_returns_file_confirm")
NS = "urn:iso:std:iso:20022:tech:xsd:pain.002.001.03"


def tx(reference, code="AM04", *, status="RJCT", amount=None, fee=None):
    amount_xml = (
        f'<OrgnlTxRef><Amt><InstdAmt Ccy="EUR">{amount}</InstdAmt></Amt></OrgnlTxRef>'
        if amount
        else ""
    )
    fee_xml = f'<ChrgsInf><Amt Ccy="EUR">{fee}</Amt></ChrgsInf>' if fee else ""
    return (
        f"<TxInfAndSts><OrgnlEndToEndId>{reference}</OrgnlEndToEndId><TxSts>{status}</TxSts>"
        f"<StsRsnInf><Rsn><Cd>{code}</Cd></Rsn></StsRsnInf>{fee_xml}{amount_xml}</TxInfAndSts>"
    )


def pain002(*txs) -> bytes:
    return (
        f'<?xml version="1.0" encoding="UTF-8"?><Document xmlns="{NS}"><CstmrPmtStsRpt>'
        "<GrpHdr><MsgId>RET-PROVA-1</MsgId></GrpHdr>"
        f"<OrgnlPmtInfAndSts><OrgnlPmtInfId>PROVA</OrgnlPmtInfId>{''.join(txs)}</OrgnlPmtInfAndSts>"
        "</CstmrPmtStsRpt></Document>"
    ).encode()


def test_llegeix_els_rebuts_rebutjats_i_ignora_la_resta():
    data = pain002(
        tx("R1", "am04", amount="35.00", fee="3.00"), tx("R2", status="ACCP"), tx("R3", "MD01")
    )
    assert bank_returns.parse(data) == [
        {"end_to_end_id": "R1", "reason_code": "AM04", "amount_cents": 3500, "fee_cents": 300},
        {"end_to_end_id": "R3", "reason_code": "MD01", "amount_cents": None, "fee_cents": None},
    ]


@pytest.mark.parametrize(
    "data",
    [
        b"no es xml",
        b'<?xml version="1.0"?><Document><Altre/></Document>',
        pain002(tx("R1", status="ACCP")),  # cap retornat
        pain002(tx("R1"), tx("R1")),  # referència repetida
        pain002(tx("", "AM04")),  # sense referència
        pain002(tx("R1", amount="35.001")),  # import
        pain002(tx("R1", amount="-3")),
        pain002(tx("R1", amount="NaN")),
        pain002(tx("R1", fee="Infinity")),
        pain002(tx("R1", amount="35.00").replace("EUR", "USD")),  # moneda
        b'<?xml version="1.0"?><!DOCTYPE d [<!ENTITY a "x">]><Document>&a;</Document>',
    ],
)
def test_un_fitxer_trencat_es_rebutja_sencer(data):
    with pytest.raises(bank_returns.Rejected):
        bank_returns.parse(data)


def test_comissio_zero_i_codi_no_reconegut_no_rebutgen_el_fitxer():
    data = pain002(tx("R1", fee="0.00"), tx("R2", "AM4")).replace(
        b"<Cd>AM4</Cd>", b"<Prtry>PROPI</Prtry>"
    )
    first, second = bank_returns.parse(data)
    assert first["fee_cents"] is None
    assert second["reason_code"] == ""


def test_codi_no_reconegut_queda_per_entrar_a_ma(collected, treasurer):  # noqa: F811
    data = pain002(tx(collected[0].end_to_end_id, "AM4"), tx(collected[1].end_to_end_id))
    result = bank_returns.preview(data, by=treasurer)
    assert result["counts"] == {"bad_code": 1, "ready": 1}


def test_previsualitza_i_confirma_tot_alhora(collected, treasurer):  # noqa: F811
    first, second = collected  # 3500 i 9000
    data = pain002(
        tx(first.end_to_end_id, amount="35.00", fee="3.00"),
        tx(second.end_to_end_id, "MD01"),
        tx("R-NO-EXISTEIX"),
    )
    result = bank_returns.preview(data, by=treasurer)
    assert result["counts"] == {"ready": 2, "unknown": 1}
    assert not DirectDebitItem.objects.filter(status="returned").exists()  # encara res

    assert bank_returns.confirm(result["token"], by=treasurer) == {
        returns.RETRY: 1,
        returns.SENT: 1,
    }
    assert set(DirectDebitItem.objects.filter(status="returned").values_list("pk", flat=True)) == {
        first.pk,
        second.pk,
    }
    assert Movement.objects.get(kind="fee").amount_cents == 300
    assert AuditEntry.objects.filter(action="payments.returns_file.imported").count() == 1

    again = bank_returns.preview(data, by=treasurer)  # el mateix fitxer, una altra vegada
    assert again["counts"] == {"done": 2, "unknown": 1} and again["token"] == ""
    with pytest.raises(bank_returns.Stale):  # i el testimoni vell ja no registra res
        bank_returns.confirm(result["token"], by=treasurer)


def test_import_diferent_no_es_registra(collected, treasurer):  # noqa: F811
    result = bank_returns.preview(
        pain002(tx(collected[0].end_to_end_id, amount="1.00")), by=treasurer
    )
    assert result["counts"] == {"error": 1} and result["token"] == ""


def test_si_un_rebut_canvia_no_se_n_registra_cap(collected, treasurer):  # noqa: F811
    first, second = collected
    result = bank_returns.preview(
        pain002(tx(first.end_to_end_id), tx(second.end_to_end_id)), by=treasurer
    )
    returns.register_return(second, "AM04", by=treasurer)  # entrat a mà entremig
    with pytest.raises(bank_returns.Stale):
        bank_returns.confirm(result["token"], by=treasurer)
    assert DirectDebitItem.objects.get(pk=first.pk).status == DirectDebitItem.Status.COLLECTED
    assert Charge.objects.get(pk=first.attempt.charge_id).status == Charge.Status.PAID


def test_un_testimoni_manipulat_no_val(collected, treasurer):  # noqa: F811
    token = bank_returns.preview(pain002(tx(collected[0].end_to_end_id)), by=treasurer)["token"]
    with pytest.raises(bank_returns.Stale):
        bank_returns.confirm(token[:-2] + "xx", by=treasurer)


def test_sense_b4_amb_edicio_no_trobat(collected, make_admin):  # noqa: F811
    other = make_admin(Role.Code.PRESIDENT)
    with pytest.raises(Http404):
        bank_returns.preview(pain002(tx(collected[0].end_to_end_id)), by=other)
    with pytest.raises(Http404):
        bank_returns.confirm("x", by=other)


def test_el_tipus_xml_nomes_val_per_als_retornats():
    upload = SimpleUploadedFile("retornats.xml", pain002(tx("R1")))
    bare = pain002(tx("R1")).split(b"?>", 1)[1]  # la declaració XML és opcional
    assert files.validate_upload(
        SimpleUploadedFile("r.xml", b"\xef\xbb\xbf\n" + bare), allowed=files.BANK_RETURNS_TYPES
    )
    assert files.validate_upload(upload, allowed=files.BANK_RETURNS_TYPES) == "application/xml"
    for allowed in (files.IMPORT_TYPES, files.BANK_STATEMENT_TYPES, files.UPLOAD_TYPES):
        with pytest.raises(files.ValidationError):
            files.validate_upload(upload, allowed=allowed)
    with pytest.raises(files.ValidationError):  # XML amb una altra extensió
        files.validate_upload(
            SimpleUploadedFile("r.csv", pain002(tx("R1"))), allowed=files.IMPORT_TYPES
        )


def test_pantalla_puja_previsualitza_i_confirma(collected, treasurer):  # noqa: F811
    client = client_for(treasurer)
    assert "Importa el fitxer de retornats del banc" in main_of(client.get(URL).content.decode())
    upload = SimpleUploadedFile("retornats.xml", pain002(tx(collected[0].end_to_end_id, "AM04")))

    response = client.post(FILE_URL, {"fitxer": upload})

    html = main_of(response.content.decode())
    assert response.status_code == 200 and "Es registrarà 1 retorn" in html
    token = response.context["file_preview"]["token"]
    response = client.post(CONFIRM_URL, {"testimoni": token}, follow=True)
    html = main_of(response.content.decode())
    assert "Fitxer registrat: 1 retorn." in html and "Reintent (intent 2)" in html


def test_pantalla_errors_del_fitxer(collected, treasurer):  # noqa: F811
    client = client_for(treasurer)
    response = client.post(FILE_URL, {"fitxer": SimpleUploadedFile("r.xml", b"<?xml x")})
    assert response.status_code == 400 and "No és un fitxer XML vàlid." in response.content.decode()
    response = client.post(FILE_URL, {"fitxer": SimpleUploadedFile("r.pdf", b"%PDF-1.4")})
    assert response.status_code == 400
    response = client.post(CONFIRM_URL, {"testimoni": "manipulat"}, follow=True)
    assert "Torna a pujar el fitxer" in main_of(response.content.decode())


@pytest.mark.parametrize(
    "role", [c for c in Role.Code.values if c not in ("member", "visitor", "guest")]
)
def test_b4_cella_de_cada_rol_al_fitxer(make_admin, role, collected):  # noqa: F811
    client = client_for(make_admin(role))
    allowed = role == Role.Code.TREASURER
    upload = SimpleUploadedFile("retornats.xml", pain002(tx(collected[0].end_to_end_id)))
    assert client.post(FILE_URL, {"fitxer": upload}).status_code == (200 if allowed else 404)
    assert client.post(CONFIRM_URL, {"testimoni": "x"}).status_code == (302 if allowed else 404)
