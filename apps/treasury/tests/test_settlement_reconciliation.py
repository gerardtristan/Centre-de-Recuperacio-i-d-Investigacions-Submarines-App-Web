"""La línia del banc pel net d'una liquidació del proveïdor: proposta, confirmació des de la
conciliació i desfer-la (T-M04-13b; P-M04-F, passos 2 a 4; CA-T11.1; RN-T16, RN-T17, RN-T25;
P-364 i P-365). Només dades inventades."""

from dataclasses import replace
from datetime import date

import pytest
from django.http import Http404
from django.urls import reverse

from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import main_of
from apps.core.tests.conftest import make_admin as _make_admin
from apps.treasury import reconciliation, settlements
from apps.treasury.models import (
    Movement,
    ProviderSettlement,
    Reconciliation,
    ReconciliationUndo,
    StatementLineState,
)
from apps.treasury.settlements import SettlementLine
from apps.treasury.tests import test_settlements as base
from apps.treasury.tests.test_reconciliation import lines
from apps.treasury.tests.test_reconciliation_undo import bank_balance
from apps.treasury.tests.test_views import client_for

pytestmark = pytest.mark.django_db
# Fixtures compartides (assignades, no importades, perquè els paràmetres no les tapin).
make_admin, person, transit, treasurer, two = (
    _make_admin,
    base.person,
    base.transit,
    base.treasurer,
    base.two,
)
collected, data, record_it = base.collected, base.data, base.record_it
K = Movement.Kind
State = StatementLineState.Status
Status = ProviderSettlement.Status
NET = 12380  # brut 12.500 − comissions 120 (M04-7)
REASON = "Casada amb una altra liquidació (prova)"


def received(*items, external_id="LIQ-001", settled_on=date(2026, 11, 1)):
    """Liquidació rebuda; les línies de `lines` són del 2 de novembre en endavant."""
    return record_it(replace(data(*items, external_id=external_id), settled_on=settled_on))


def another_with_the_same_net(person):
    collected(person, 12500, "REF-C")
    return received(SettlementLine("REF-C", 12500), external_id="LIQ-002")


def proposal(line):
    found = StatementLineState.objects.get(statement_line=line)
    return found.status, found.review_reason, found.proposed_settlement


def bank_line(by, concept="ABONAMENT PROVEIDOR", amount=NET):
    (line,) = lines(by, (amount, concept))
    reconciliation.refresh()
    return line


class TestProposal:
    def test_ca_t11_1_the_net_within_the_window_is_proposed_and_nothing_is_booked(
        self,
        two,
        treasurer,
    ):
        settlement = received()
        line = bank_line(treasurer)
        assert proposal(line) == (State.PROPOSED, "", settlement)
        assert not Movement.objects.filter(kind__in=[K.FEE, K.TRANSFER]).exists()
        assert ProviderSettlement.objects.get().status == Status.RECEIVED

    @pytest.mark.parametrize(
        ("amount", "settled_on"),
        [
            (NET + 1, date(2026, 11, 1)),  # un cèntim de més
            (NET, date(2026, 11, 3)),  # la línia és d'abans de la liquidació
            (NET, date(2026, 10, 27)),  # més de 5 dies després (P-364)
        ],
    )
    def test_another_amount_or_out_of_the_window_is_not_proposed(
        self,
        two,
        treasurer,
        amount,
        settled_on,
    ):
        received(settled_on=settled_on)
        line = bank_line(treasurer, amount=amount)
        assert proposal(line) == (State.PENDING, "", None)

    def test_two_settlements_with_the_same_net_go_to_review(self, two, person, treasurer):
        received()
        another_with_the_same_net(person)
        line = bank_line(treasurer)
        assert proposal(line) == (State.PENDING, reconciliation.AMBIGUOUS, None)
        assert line.pk in [s.statement_line_id for s in reconciliation.to_review()]

    def test_the_identifier_in_the_concept_picks_one(self, two, person, treasurer):
        received()
        other = another_with_the_same_net(person)
        line = bank_line(treasurer, concept="ABONAMENT liq-002 PROVEIDOR")
        assert proposal(line) == (State.PROPOSED, "", other)

    def test_one_settlement_for_two_lines_goes_to_review(self, two, treasurer):
        received()
        first, second = lines(treasurer, (NET, "ABONAMENT"), (NET, "ABONAMENT"))
        reconciliation.refresh()
        assert proposal(first)[1] == proposal(second)[1] == reconciliation.AMBIGUOUS

    def test_a_confirmed_settlement_is_no_longer_proposed(self, two, treasurer):
        settlements.confirm(received(), by=treasurer)
        assert proposal(bank_line(treasurer)) == (State.PENDING, "", None)


class TestConfirmLine:
    def test_fees_transfer_and_the_line_reconciled(self, two, transit, treasurer):
        settlement = received()
        line = bank_line(treasurer)
        settlements.confirm_line(line, settlement.pk, by=treasurer)
        settlement.refresh_from_db()
        assert settlement.status == Status.RECONCILED
        fees = sorted(m.amount_cents for m in Movement.objects.filter(kind=K.FEE))
        assert fees == [33, 87]
        out, entry = Movement.objects.filter(kind=K.TRANSFER).order_by("pk")
        assert (out.account, out.amount_cents, entry.account.kind) == (transit, NET, "bank")
        assert bank_balance() == NET
        found = Reconciliation.objects.get()
        assert (found.statement_line, found.settlement, found.confirmed_by) == (
            line,
            settlement,
            treasurer,
        )
        assert set(found.matched_charges.all()) == {two[0].charge, two[1].charge}
        assert proposal(line) == (State.RECONCILED, "", settlement)
        entry = AuditEntry.objects.get(action=settlements.CONFIRMED)
        assert (entry.actor_account, entry.details["line"]) == (treasurer, line.pk)

    def test_another_settlement_than_the_proposed_one_is_rejected(self, two, treasurer):
        settlement = received()
        line = bank_line(treasurer)
        with pytest.raises(settlements.SettlementRejected):
            settlements.confirm_line(line, settlement.pk + 1, by=treasurer)
        assert not Movement.objects.filter(kind__in=[K.FEE, K.TRANSFER]).exists()
        assert not Reconciliation.objects.exists()

    def test_the_transfer_confirmation_does_not_take_it(self, two, treasurer):
        received()
        line = bank_line(treasurer)
        with pytest.raises(reconciliation.ReconciliationRejected):
            reconciliation.confirm(line, by=treasurer)
        assert not Reconciliation.objects.exists()

    def test_only_with_t4(self, two, treasurer, make_admin):
        settlement = received()
        line = bank_line(treasurer)
        for role in ("administrator", "secretary"):
            with pytest.raises(Http404):
                settlements.confirm_line(line, settlement.pk, by=make_admin(role))
        assert proposal(line)[0] == State.PROPOSED


class TestUndo:
    def test_the_transfer_is_reversed_the_fees_stay_and_it_is_proposed_again(
        self,
        two,
        transit,
        treasurer,
    ):
        settlement = received()
        line = bank_line(treasurer)
        settlements.confirm_line(line, settlement.pk, by=treasurer)
        done = reconciliation.undo(Reconciliation.objects.get(), reason=REASON, by=treasurer)
        assert (done.reason, done.undone_by) == (REASON, treasurer)
        legs = Movement.objects.filter(kind=K.TRANSFER)
        assert all(leg.is_reversed for leg in legs)
        assert {r.reason for r in Movement.objects.filter(kind=K.REVERSAL)} == {REASON}
        assert bank_balance() == 0
        assert Movement.objects.filter(kind=K.FEE).count() == 2  # P-365
        settlement.refresh_from_db()
        assert settlement.status == Status.RECEIVED
        assert proposal(line) == (State.PROPOSED, "", settlement)
        assert AuditEntry.objects.get(action=reconciliation.UNDONE).reason == REASON
        # Es torna a confirmar sense repetir les comissions.
        settlements.confirm_line(line, settlement.pk, by=treasurer)
        assert Movement.objects.filter(kind=K.FEE).count() == 2
        assert bank_balance() == NET

    def test_twice_is_rejected(self, two, treasurer):
        settlement = received()
        settlements.confirm_line(bank_line(treasurer), settlement.pk, by=treasurer)
        found = Reconciliation.objects.get()
        reconciliation.undo(found, reason=REASON, by=treasurer)
        with pytest.raises(reconciliation.ReconciliationRejected):
            reconciliation.undo(found, reason=REASON, by=treasurer)
        assert ReconciliationUndo.objects.count() == 1


class TestScreens:
    def url(self, line):
        return reverse("administration:treasury_confirm_settlement_line", args=[line.pk])

    def test_review_then_confirm_then_undo(self, two, treasurer):
        settlement = received()
        line = bank_line(treasurer, concept="ABONAMENT M INVENTADA")
        client = client_for(treasurer)
        page = reverse("administration:treasury_reconciliation")
        html = main_of(client.get(page).content.decode())
        assert "LIQ-001" in html and "Revisa i confirma…" in html
        html = main_of(client.get(self.url(line)).content.decode())
        # P-M04-F, pas 3: brut, comissions amb el repartiment i net; dels cobraments, cap nom.
        assert "125,00" in html and "0,87" in html and "0,33" in html and "123,80" in html
        assert "REF-A" in html and "Coll" not in html
        response = client.post(self.url(line), {"liquidacio": settlement.pk}, follow=True)
        assert "Liquidació conciliada" in response.content.decode()
        assert proposal(line)[0] == State.RECONCILED
        done = Reconciliation.objects.get()
        undo = reverse("administration:treasury_undo_reconciliation", args=[done.pk])
        response = client.post(undo, {"motiu": REASON}, follow=True)
        assert "la liquidació torna a «rebuda»" in response.content.decode()

    def test_without_t4_it_is_not_found(self, two, treasurer, make_admin):
        settlement = received()
        line = bank_line(treasurer)
        for role in (Role.Code.ADMINISTRATOR, Role.Code.SECRETARY):
            client = client_for(make_admin(role))
            assert client.get(self.url(line)).status_code == 404
            assert client.post(self.url(line), {"liquidacio": settlement.pk}).status_code == 404
        assert not Reconciliation.objects.exists()

    def test_the_post_needs_csrf(self, two, treasurer):
        settlement = received()
        line = bank_line(treasurer)
        client = client_for(treasurer)
        client.handler.enforce_csrf_checks = True
        assert client.post(self.url(line), {"liquidacio": settlement.pk}).status_code == 403
        assert not Reconciliation.objects.exists()

    def test_a_line_without_a_settlement_goes_back_with_a_message(self, treasurer):
        line = bank_line(treasurer)
        response = client_for(treasurer).get(self.url(line), follow=True)
        assert "no té cap liquidació proposada" in response.content.decode()
