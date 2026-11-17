"""Rebuts domiciliats retornats: reintent i alternativa (T-M05b-12; CA-M05b-18, 19 i 20;
RN-M05b-14 i 15). Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.utils import timezone

from apps.core import imports
from apps.core.models import AuditEntry, Charge, OutgoingEmail, Role, Setting
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.services import FEE_RETURNED
from apps.payments import remittances, returns, sepa_xml
from apps.payments.models import DirectDebitItem, PaymentAttempt, ReceiptCancellation, SepaMandate
from apps.payments.tests.test_remittance_settlement import (  # noqa: F401 (fixtures)
    club,
    sent,
    treasurer,
)
from apps.payments.tests.test_remittances import (  # noqa: F401 (fixtures)
    collection_date,
    signer,
    text,
)
from apps.treasury.models import Movement

pytestmark = pytest.mark.django_db


def settle(remittance, by, n=1):
    """Liquida la remesa amb una línia d'extracte inventada (`n` canvia l'empremta del lot)."""
    batch = imports.open_confirmed(
        "bank_statement", file_sha256=str(n) * 64, by=by, counts={"new_count": 1}
    )
    row = {
        "row": 2,
        "result": "new",
        "value_date": remittance.collection_date,
        "amount_cents": remittance.total_cents,
        "concept": "ABONO REMESA",
        "balance_cents": None,
    }
    imports.add_lines(batch, [row])
    return remittances.settle_remittance(remittance, imports.statement_lines(batch).get(), by=by)


@pytest.fixture
def collected(sent, treasurer):  # noqa: F811
    settle(sent, treasurer)
    items = DirectDebitItem.objects.filter(remittance=sent).order_by("amount_cents")
    return list(items)  # 3500, 9000


def test_ca_m05b_18_fons_insuficients_proposa_un_reintent(collected, treasurer):  # noqa: F811
    item = collected[0]

    proposal = returns.register_return(item, "am04", fee_cents=300, by=treasurer)

    assert proposal == returns.RETRY
    item.refresh_from_db()
    charge = item.attempt.charge
    assert (item.status, item.return_reason_code) == ("returned", "AM04")
    assert item.returned_on == timezone.localdate()
    assert charge.status == Charge.Status.RETURNED
    assert item.attempt.status == PaymentAttempt.Status.CANCELLED
    assert ReceiptCancellation.objects.filter(receipt__attempt=item.attempt).exists()
    returned = Movement.objects.get(kind="return", payment__charge=charge)
    assert returned.amount_cents == 3500
    assert Movement.objects.get(kind="fee", linked_movement=returned).amount_cents == 300
    assert AuditEntry.objects.filter(action=FEE_RETURNED).count() == 1  # avís al tresorer

    returns.confirm(item, returns.RETRY, by=treasurer)

    charge.refresh_from_db()
    assert charge.status == Charge.Status.PENDING
    reopened = AuditEntry.objects.filter(
        action="charges.status_changed", reason__contains="Reintent"
    )
    assert reopened.exists()
    assert not OutgoingEmail.objects.filter(template=returns.ALTERNATIVE_TEMPLATE).exists()
    # La quota torna a la remesa següent com a intent 2 de 2.
    second = remittances.build_remittance("2026-12-R", collection_date(), treasurer)
    assert second.items.get().attempt_number == 2


def test_ca_m05b_19_el_segon_retorn_no_proposa_cap_reintent(collected, treasurer):  # noqa: F811
    returns.register_return(collected[0], "AM04", by=treasurer)
    returns.confirm(collected[0], returns.RETRY, by=treasurer)
    second = remittances.build_remittance("2026-12-R", collection_date(), treasurer)
    sepa_xml.remittance_file(second, treasurer)
    remittances.mark_remittance_sent(second, file_deleted=True, by=treasurer)
    settle(second, treasurer, n=2)  # l'intent nou es pot pagar: l'anterior és «cancel·lat»
    retry = second.items.get()

    assert returns.register_return(retry, "AM04", by=treasurer) == returns.ALTERNATIVE
    with pytest.raises(returns.RetryNotAllowed):
        returns.confirm(retry, returns.RETRY, by=treasurer)
    assert returns.confirm(retry, returns.ALTERNATIVE, by=treasurer)

    email = OutgoingEmail.objects.get(template=returns.ALTERNATIVE_TEMPLATE)
    assert email.to_address == "soci1@example.org"
    assert f"/socis/pagaments/{retry.attempt.charge_id}/" in email.body_text
    assert "mandat" not in email.body_text
    # Cap tercer rebut (RN-M05b-30).
    excluded = dict(remittances.preview(collection_date()).excluded)
    assert excluded[retry.attempt.charge.annual_fee] == remittances.EXHAUSTED


def test_ca_m05b_20_compte_tancat_bloqueja_el_mandat(collected, treasurer):  # noqa: F811
    item = collected[1]

    assert returns.register_return(item, "AC04", by=treasurer) == returns.ALTERNATIVE

    item.mandate.refresh_from_db()
    assert item.mandate.status == SepaMandate.Status.BLOCKED
    with pytest.raises(returns.RetryNotAllowed):
        returns.confirm(item, returns.RETRY, by=treasurer)
    returns.confirm(item, returns.ALTERNATIVE, by=treasurer)
    email = OutgoingEmail.objects.get(template=returns.ALTERNATIVE_TEMPLATE)
    assert "/socis/pagaments/mandat/" in email.body_text
    assert "AC04" not in email.body_text
    excluded = dict(remittances.preview(collection_date()).excluded)
    assert excluded[item.attempt.charge.annual_fee] == remittances.NO_MANDATE


def test_refus_del_deutor_i_codi_desconegut_van_a_l_alternativa(collected, treasurer):  # noqa: F811
    assert returns.register_return(collected[0], "MS02", by=treasurer) == returns.ALTERNATIVE
    assert returns.register_return(collected[1], "ZZ99", by=treasurer) == returns.ALTERNATIVE
    assert SepaMandate.objects.filter(status="active").count() == 2


def test_nomes_amb_b4_i_sense_canvis_si_no(collected, treasurer, make_admin):  # noqa: F811
    with pytest.raises(Http404):
        returns.register_return(collected[0], "AM04", by=make_admin(Role.Code.SECRETARY))
    collected[0].refresh_from_db()
    assert collected[0].status == "collected"
    assert not Movement.objects.filter(kind="return").exists()


def test_errors_d_entrada(sent, collected, treasurer):  # noqa: F811
    with pytest.raises(ValidationError):
        returns.register_return(collected[0], "A4", by=treasurer)
    with pytest.raises(returns.NotReturned):  # encara no s'ha retornat
        returns.confirm(collected[0], returns.RETRY, by=treasurer)
    returns.register_return(collected[0], "AM04", by=treasurer)
    with pytest.raises(returns.NotCollected):  # dues vegades, no
        returns.register_return(collected[0], "AM04", by=treasurer)
    returns.confirm(collected[0], returns.ALTERNATIVE, by=treasurer)
    with pytest.raises(ValidationError):  # el càrrec ja és «pendent»
        returns.confirm(collected[0], returns.ALTERNATIVE, by=treasurer)


def test_el_maxim_d_intents_es_l_ajust_vc_16(collected, treasurer):  # noqa: F811
    Setting.objects.filter(key=returns.MAX_ATTEMPTS).update(initial_value=1)

    assert returns.register_return(collected[0], "AM04", by=treasurer) == returns.ALTERNATIVE
    returns.confirm(collected[0], returns.ALTERNATIVE, by=treasurer)
    excluded = dict(remittances.preview(collection_date()).excluded)
    assert excluded[collected[0].attempt.charge.annual_fee] == remittances.EXHAUSTED
