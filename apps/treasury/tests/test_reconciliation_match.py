"""Casar a mà una línia de l'extracte amb un o més càrrecs (T-M04-12e; P-M04-E pas 3; LT2;
RN-T16, RN-T17, RN-T17b). Només dades inventades."""

import pytest
from django.db import connection
from django.http import Http404
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.core import charges
from apps.core.models import AuditEntry, Charge, Payment, Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.members.models import Member
from apps.members.tests.test_cards import add_fee, make_member
from apps.payments import attempts, remittances
from apps.payments.models import PaymentAttempt
from apps.payments.tests.test_remittances import new_member, signer, text  # noqa: F401
from apps.treasury import reconciliation
from apps.treasury.models import (
    Movement,
    Reconciliation,
    StatementLineState,
    TransferReference,
)
from apps.treasury.tests.test_reconciliation import SYSTEM, charge, lines, ref, state  # noqa: F401
from apps.treasury.tests.test_views import MANAGEMENT_ROLES, client_for

pytestmark = pytest.mark.django_db
State = StatementLineState.Status
Rejected = reconciliation.ReconciliationRejected
REASON = "Casada amb el càrrec equivocat (prova)"


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin(Role.Code.TREASURER)


def no_money_moved():
    return not Payment.objects.exists() and not Movement.objects.exists()


class TestMatch:
    def test_lt2_a_line_without_reference_is_matched_with_several_charges(self, treasurer, charge):  # noqa: F811
        first, second, other = charge(9000), charge(3500), charge(3500)
        (line,) = lines(treasurer, (12500, "TRANSF SENSE REFERENCIA"))
        done = reconciliation.match(line, [second.pk, first.pk], by=treasurer)
        assert set(done.matched_charges.all()) == {first, second}
        assert done.confirmed_by == treasurer
        assert Charge.objects.get(pk=other.pk).status == Charge.Status.PENDING
        for paid in (first, second):
            paid.refresh_from_db()
            assert paid.status == Charge.Status.PAID
            payment = Payment.objects.get(charge=paid)
            assert payment.method == Payment.Method.TRANSFER
            assert payment.transfer_reference == ""  # la línia no en portava cap
        assert not TransferReference.objects.exists()
        incomes = Movement.objects.filter(kind="income", account__kind="bank")
        assert sorted(incomes.values_list("amount_cents", flat=True)) == [3500, 9000]
        assert state(line) == (State.RECONCILED, "", [first, second])
        entry = AuditEntry.objects.get(action=reconciliation.CONFIRMED)
        assert entry.actor_account == treasurer
        assert entry.details["manual"] is True and entry.details["amount_cents"] == 12500

    def test_a_line_to_review_with_another_amount_is_matched_with_the_right_charges(
        self,
        treasurer,
        charge,  # noqa: F811
    ):
        quota, extra = charge(9000), charge(1000)
        (line,) = lines(treasurer, (10000, f"TRANSF {ref(quota)}"))
        reconciliation.refresh()
        assert state(line)[1] == StatementLineState.ReviewReason.AMOUNT_MISMATCH
        reconciliation.match(line, [quota.pk, extra.pk], by=treasurer)
        assert state(line)[0] == State.RECONCILED
        # Només la referència que porta la línia; a l'altre càrrec no se n'inventa cap.
        assert Payment.objects.get(charge=quota).transfer_reference == ref(quota)
        assert Payment.objects.get(charge=extra).transfer_reference == ""
        assert not TransferReference.objects.filter(charge=extra).exists()

    def test_a_fee_activates_the_member(self, treasurer):
        member = make_member(status=Member.Status.PENDING)
        fee = add_fee(member)
        (line,) = lines(treasurer, (9000, "INGRES SOCI"))
        reconciliation.match(line, [fee.charge.pk], by=treasurer)
        member.refresh_from_db()
        assert member.status == Member.Status.ACTIVE

    @pytest.mark.parametrize("amount", [8999, 9001])
    def test_rn_t17_the_sum_must_be_exact(self, treasurer, charge, amount):  # noqa: F811
        quota = charge(9000)
        (line,) = lines(treasurer, (amount, "TRANSF"))
        with pytest.raises(Rejected, match="han de coincidir"):
            reconciliation.match(line, [quota.pk], by=treasurer)
        assert no_money_moved() and not Reconciliation.objects.exists()

    def test_a_charge_that_is_not_pending_is_refused(self, treasurer, charge):  # noqa: F811
        cancelled, paid = charge(9000), charge(9000)
        charges.cancel(cancelled, "Anul·lada (prova)", by=SYSTEM)
        (done_line, line) = lines(
            treasurer, (9000, f"TRANSF {ref(paid)}"), (9000, "TRANSF SENSE REFERENCIA")
        )
        reconciliation.confirm(done_line, by=treasurer)
        for taken in (cancelled, paid):
            with pytest.raises(Rejected, match="ja no està pendent"):
                reconciliation.match(line, [taken.pk], by=treasurer)
        assert Reconciliation.objects.count() == 1

    def test_a_charge_proposed_for_another_line_is_refused(self, treasurer, charge):  # noqa: F811
        quota = charge(9000)
        proposed, line = lines(treasurer, (9000, f"TRANSF {ref(quota)}"), (9000, "TRANSF"))
        with pytest.raises(Rejected, match="proposta d'una altra línia"):
            reconciliation.match(line, [quota.pk], by=treasurer)
        assert no_money_moved()
        reconciliation.refresh()
        assert state(proposed)[0] == State.PROPOSED

    def test_only_a_pending_incoming_line_of_a_current_statement(self, treasurer, charge):  # noqa: F811
        quota = charge(9000)
        out, excluded, done, proposed = lines(
            treasurer,
            (-9000, "REBUT"),
            (9000, "INGRES"),
            (9000, "TRANSF"),
            (9000, f"TRANSF {ref(charge(9000))}"),
        )
        reconciliation.refresh()
        reconciliation.exclude(excluded, reason="No és del club", by=treasurer)
        reconciliation.match(done, [quota.pk], by=treasurer)
        with pytest.raises(Rejected, match="no es pot casar"):
            reconciliation.match(out, [charge(9000).pk], by=treasurer)
        for line in (excluded, done, proposed):
            with pytest.raises(Rejected, match="no es pot casar"):
                reconciliation.match(line, [charge(9000).pk], by=treasurer)
        assert Reconciliation.objects.count() == 1

    def test_a_line_that_now_has_a_proposal_says_so(self, treasurer, charge):  # noqa: F811
        quota = charge(9000)
        (line,) = lines(treasurer, (9000, f"TRANSF {ref(quota)}"))
        with pytest.raises(Rejected, match="ja té una proposta: revisa-la i confirma-la"):
            reconciliation.match(line, [quota.pk], by=treasurer)

    def test_no_charge_or_an_unknown_one_is_refused(self, treasurer):
        (line,) = lines(treasurer, (9000, "TRANSF"))
        for ids in ([], [999999]):
            with pytest.raises(Rejected, match="Tria un o més"):
                reconciliation.match(line, ids, by=treasurer)

    def test_rn_t16_only_with_t4(self, treasurer, make_admin, charge):  # noqa: F811
        quota = charge(9000)
        (line,) = lines(treasurer, (9000, "TRANSF"))
        for who in (make_admin("administrator"), make_admin("secretary"), SYSTEM):
            for call in (reconciliation.match, reconciliation.check_match):
                with pytest.raises(Http404):
                    call(line, [quota.pk], by=who)
        assert no_money_moved()

    def test_045_a_manual_match_is_undone_and_the_line_goes_back(self, treasurer, charge):  # noqa: F811
        quota = charge(9000)
        (line,) = lines(treasurer, (9000, "TRANSF SENSE REFERENCIA"))
        done = reconciliation.match(line, [quota.pk], by=treasurer)
        reconciliation.undo(done, reason=REASON, by=treasurer)
        quota.refresh_from_db()
        assert quota.status == Charge.Status.PENDING
        assert Movement.objects.filter(kind="reversal").count() == 1
        assert state(line)[0] == State.PENDING
        # Es pot tornar a casar, ara bé.
        reconciliation.match(line, [quota.pk], by=treasurer)
        assert Reconciliation.objects.filter(undo__isnull=True).count() == 1


class TestPendingCharges:
    def search(self, query):
        return reconciliation.pending_charges(query)[0]

    def test_by_reference_or_member_number_only_pending(self, charge):  # noqa: F811
        member = make_member(number=4321)
        fee = add_fee(member)
        quota, cancelled = charge(9000), charge(9000)
        charges.cancel(cancelled, "Anul·lada (prova)", by=SYSTEM)
        reference = ref(quota)
        assert self.search(reference) == [quota]
        assert self.search(reference.lower().replace("-", " ")) == [quota]
        assert self.search(ref(cancelled)) == []
        assert self.search("4321") == [fee.charge]
        # Els més recents primer.
        assert self.search(f"4321, {reference}") == [quota, fee.charge]
        assert self.search("Prova") == []  # cap cerca per nom
        assert self.search("") == self.search("²") == []

    def test_more_than_the_limit_says_so(self):
        member = make_member(number=4321)
        fees = [add_fee(member, period=year) for year in range(2000, 2022)]
        found, more = reconciliation.pending_charges("4321")
        assert more and len(found) == reconciliation.SEARCH_LIMIT
        assert found[0] == fees[-1].charge  # la més recent
        assert reconciliation.pending_charges(ref(fees[0].charge)) == ([fees[0].charge], False)


def sent_remittance_fee(signer, text, treasurer):  # noqa: F811
    """Una quota en una remesa enviada al banc: el banc la cobrarà sola."""
    fee = new_member(1, signer=signer, text=text)
    remittances.build_remittance("2026-12", remittances.earliest_collection_date(), treasurer)
    return fee


class TestNoDoubleCharge:
    def test_a_fee_in_a_remittance_is_not_matched(self, treasurer, signer, text):  # noqa: F811
        fee = sent_remittance_fee(signer, text, treasurer)
        (line,) = lines(treasurer, (9000, "TRANSF"))
        with pytest.raises(Rejected, match="cobrament en curs"):
            reconciliation.match(line, [fee.charge.pk], by=treasurer)
        assert not Payment.objects.exists()
        (found,), _more = reconciliation.pending_charges("1")
        assert found.collecting

    def test_a_card_in_progress_blocks_but_a_waiting_transfer_does_not(self, treasurer, charge):  # noqa: F811
        by_card, by_transfer = charge(9000), charge(3500)
        for which, method in ((by_card, "card"), (by_transfer, "transfer")):
            attempts.transition(
                attempts.create_attempt(which, method),
                PaymentAttempt.Status.IN_PROGRESS,
                by=SYSTEM,
            )
        first, second = lines(treasurer, (9000, "TRANSF"), (3500, "TRANSF"))
        with pytest.raises(Rejected, match="cobrament en curs"):
            reconciliation.match(first, [by_card.pk], by=treasurer)
        reconciliation.match(second, [by_transfer.pk], by=treasurer)
        assert PaymentAttempt.objects.get(charge=by_transfer).status == PaymentAttempt.Status.PAID

    @pytest.mark.parametrize("method", ["card", "bizum"])
    def test_a_card_or_bizum_to_review_may_be_charged_and_blocks(self, treasurer, charge, method):  # noqa: F811
        quota = charge(9000)
        attempt = attempts.create_attempt(quota, method)
        attempt = attempts.transition(attempt, PaymentAttempt.Status.IN_PROGRESS, by=SYSTEM)
        attempts.transition(attempt, PaymentAttempt.Status.TO_REVIEW, by=SYSTEM)
        (line,) = lines(treasurer, (9000, "TRANSF"))
        with pytest.raises(Rejected, match="cobrament en curs"):
            reconciliation.match(line, [quota.pk], by=treasurer)
        assert not Payment.objects.exists()

    def test_the_search_shows_them_without_a_checkbox(self, treasurer, signer, text, charge):  # noqa: F811
        fee = sent_remittance_fee(signer, text, treasurer)
        proposed = charge(3500)
        line, _other = lines(treasurer, (9000, "TRANSF"), (3500, f"TRANSF {ref(proposed)}"))
        reconciliation.refresh()
        query = f"1 {ref(proposed)}"
        html = main_of(
            client_for(treasurer).get(match_url(line), {"cerca": query}).content.decode()
        )
        assert "té un cobrament en curs" in html and f'value="{fee.charge.pk}"' not in html
        assert "és a la proposta d'una altra línia" in html
        assert f'value="{proposed.pk}"' not in html


PAGE = reverse("administration:treasury_reconciliation")


def match_url(line):
    return reverse("administration:treasury_match_line", args=[line.pk])


class TestMatchView:
    @pytest.mark.parametrize("role", MANAGEMENT_ROLES)
    def test_t4_cell_of_each_role(self, make_admin, treasurer, role):  # noqa: F811
        (line,) = lines(treasurer, (9000, "TRANSF"))
        client = client_for(make_admin(role))
        expected = 200 if role == Role.Code.TREASURER else 404
        assert client.get(match_url(line)).status_code == expected
        if role != Role.Code.TREASURER:
            assert client.post(match_url(line), {"carrec": "1", "confirma": "1"}).status_code == 404

    def test_search_review_and_confirm(self, treasurer, charge):  # noqa: F811
        quota = charge(9000)
        (line,) = lines(treasurer, (9000, "TRANSF M INVENTADA"))
        client = client_for(treasurer)
        assert "Casa a mà" in main_of(client.get(PAGE).content.decode())
        html = main_of(client.get(match_url(line), {"cerca": ref(quota)}).content.decode())
        assert "M INVENTADA" in html and f'value="{quota.pk}"' in html and "IBAN" not in html
        html = main_of(client.post(match_url(line), {"carrec": quota.pk}).content.decode())
        assert "Confirma el casament" in html and no_money_moved()
        assert 'role="status"' in html and 'role="alert"' not in html  # no és cap error
        response = client.post(match_url(line), {"carrec": quota.pk, "confirma": "1"}, follow=True)
        assert "Línia casada" in response.content.decode()
        quota.refresh_from_db()
        assert quota.status == Charge.Status.PAID

    def test_a_wrong_sum_is_shown_at_the_review_and_nothing_is_paid(self, treasurer, charge):  # noqa: F811
        quota = charge(9000)
        (line,) = lines(treasurer, (9500, "TRANSF"))
        reconciliation.refresh()  # la importació ho fa en confirmar l'extracte
        client = client_for(treasurer)
        response = client.post(match_url(line), {"carrec": quota.pk, "cerca": "x"}, follow=True)
        assert "han de coincidir" in response.content.decode()
        response = client.post(match_url(line), {"carrec": "²", "confirma": "1"}, follow=True)
        assert "Tria un o més" in response.content.decode()
        assert no_money_moved()

    def test_a_failed_confirmation_comes_back_with_the_search_and_selection(
        self,
        treasurer,
        charge,  # noqa: F811
    ):
        quota = charge(9000)
        (line,) = lines(treasurer, (9000, "TRANSF"))
        client = client_for(treasurer)
        charges.cancel(quota, "Anul·lada entre la revisió i la confirmació", by=SYSTEM)
        data = {"carrec": quota.pk, "cerca": "CRIS 4321", "confirma": "1"}
        response = client.post(match_url(line), data)
        assert response["Location"].startswith(match_url(line))
        assert "cerca=CRIS+4321" in response["Location"]
        assert f"carrec={quota.pk}" in response["Location"]
        assert "ja no està pendent" in client.get(response["Location"]).content.decode()

    def test_the_selection_comes_back_checked(self, treasurer, charge):  # noqa: F811
        quota = charge(9000)
        (line,) = lines(treasurer, (9500, "TRANSF"))
        url = match_url(line)
        html = client_for(treasurer).get(url, {"cerca": ref(quota), "carrec": quota.pk})
        assert f'value="{quota.pk}" checked' in html.content.decode()

    def test_a_line_that_is_not_pending_and_incoming_says_so_without_a_form(
        self,
        treasurer,
        charge,  # noqa: F811
    ):
        quota = charge(9000)
        out, done = lines(treasurer, (-9000, "REBUT"), (9000, f"TRANSF {ref(quota)}"))
        reconciliation.confirm(done, by=treasurer)
        client = client_for(treasurer)
        for line in (out, done):
            with CaptureQueriesContext(connection) as queries:
                response = client.get(match_url(line), {"cerca": ref(quota)})
            html = main_of(response.content.decode())
            assert "no es pot casar" in html and 'name="cerca"' not in html
            # Sense cap cerca de càrrecs: ni la consulta.
            assert not [q for q in queries if "treasury_transferreference" in q["sql"]]

    def test_the_review_screen_links_here(self, treasurer, charge):  # noqa: F811
        quota = charge(9000)
        (line,) = lines(treasurer, (9500, f"TRANSF {ref(quota)}"))
        html = client_for(treasurer).get(reverse("administration:treasury_review")).content.decode()
        assert match_url(line) in html

    def test_more_results_than_the_limit_say_so(self, treasurer):
        member = make_member(number=4321)
        for year in range(2000, 2022):
            add_fee(member, period=year)
        (line,) = lines(treasurer, (9000, "TRANSF"))
        html = client_for(treasurer).get(match_url(line), {"cerca": "4321"}).content.decode()
        assert "afina la cerca" in html

    def test_post_needs_csrf(self, treasurer, charge):  # noqa: F811
        quota = charge(9000)
        (line,) = lines(treasurer, (9000, "TRANSF"))
        client = client_for(treasurer)
        client.handler.enforce_csrf_checks = True
        response = client.post(match_url(line), {"carrec": quota.pk, "confirma": "1"})
        assert response.status_code == 403
        assert no_money_moved()
