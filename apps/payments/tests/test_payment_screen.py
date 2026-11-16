"""Pantalla de pagament amb targeta i els seus estats (T-M05b-04, la resta del tall de targeta;
P-M05b-A, passos 1, 4 i 6; CA-M05b-01, 02 i 08), consulta d'estat amb HTMX i pàgina de
pagament del proveïdor fals. Només dades inventades.

Intent deixat a mitges: P-83, opció per defecte (la conservadora): no se'n comença cap altre
fins que l'anterior acabi, i la pantalla ho explica."""

import io
import re
from urllib.parse import urlsplit

import pytest
from django.test import Client, RequestFactory
from django.urls import resolve, reverse

from apps.accounts.models import Account
from apps.accounts.security import AREA_PERSONAL
from apps.core import audit, charges
from apps.core.models import AuditEntry, Charge, Payment
from apps.payments import attempts, checkout
from apps.payments.models import PaymentAttempt as Attempt
from apps.payments.models import ProviderEvent
from apps.payments.providers import base, fake
from apps.payments.tests.test_checkout import SITE, new_charge
from conftest import PASSWORD

pytestmark = pytest.mark.django_db
S = Attempt.Status
SYSTEM = audit.system("proves")
CONFIRMING = "Estem confirmant el pagament"
PAY = "Paga amb targeta"


@pytest.fixture(autouse=True)
def clean_orders(settings):
    settings.PUBLIC_SITE_URL = SITE
    fake.reset()
    yield
    fake.reset()


@pytest.fixture
def charge(personal_account):
    return new_charge(personal_account.person)


@pytest.fixture
def member(login_as, personal_account):
    return login_as(personal_account, AREA_PERSONAL)


@pytest.fixture
def sent(monkeypatch):
    """Les notificacions que la pàgina del proveïdor fals envia a la plataforma: arriben a la
    vista de l'endpoint, sense sessió (servidor a servidor). Amb `RequestFactory` i no amb un
    segon client: un client dins d'una petició del primer en tancaria la connexió."""
    received = []

    def urlopen(request, timeout):
        url = urlsplit(request.full_url)
        assert url.netloc == urlsplit(SITE).netloc
        headers = {
            f"HTTP_{name.upper().replace('-', '_')}": value
            for name, value in request.header_items()
            if name.lower() != "content-type"
        }
        posted = RequestFactory().post(url.path, request.data, "application/json", **headers)
        match = resolve(url.path)
        response = match.func(posted, *match.args, **match.kwargs)
        received.append(response.status_code)
        # No la resposta de Django: en tancar-la, enviaria `request_finished` i tancaria la
        # connexió de la prova.
        return io.BytesIO(response.content)

    monkeypatch.setattr(fake.urllib.request, "urlopen", urlopen)
    return received


def screen(charge):
    return reverse("payments:charge", args=[charge.pk])


def start(member, charge):
    return member.post(reverse("payments:pay_card", args=[charge.pk]))


def finish(attempt, status):
    return attempts.transition(attempt, status, by=SYSTEM)


class TestPaymentStatus:
    """`payments.payment_status` (M05b-5, «Estats visibles»)."""

    def test_without_attempts_it_is_pending(self, charge):
        assert checkout.payment_status(charge) == checkout.PaymentStatus(checkout.PENDING, None)

    def test_each_attempt_status_gives_what_the_member_sees(self, charge, personal_account):
        checkout.start_payment(charge, "card", personal_account)
        attempt = Attempt.objects.get()
        assert checkout.payment_status(charge).state == checkout.IN_PROGRESS
        assert checkout.payment_status(charge).attempt == attempt
        for ended, seen in ((S.FAILED, checkout.FAILED), (S.EXPIRED, checkout.FAILED)):
            finish(attempt, ended)
            assert checkout.payment_status(charge).state == seen
            checkout.start_payment(charge, "card", personal_account)
            attempt = Attempt.objects.get(status=S.IN_PROGRESS)
        finish(attempt, S.ABANDONED)  # abandonat: el càrrec torna a estar pendent
        assert checkout.payment_status(charge).state == checkout.PENDING

    def test_the_charge_decides_paid_and_closed(self, charge):
        Charge.objects.filter(pk=charge.pk).update(status=Charge.Status.PAID)
        assert checkout.payment_status(charge).state == checkout.PAID
        Charge.objects.filter(pk=charge.pk).update(status=Charge.Status.PENDING)
        charges.cancel(charge, "Duplicat (inventat)", by=SYSTEM)
        assert checkout.payment_status(charge).state == checkout.CLOSED


class TestPaymentScreen:
    def test_the_member_sees_the_amount_and_can_pay_by_card(self, member, charge, monkeypatch):
        # El testimoni CSRF és aleatori i pot contenir «cvv»: es fixa per reproduir-ho sempre.
        token = "cvv".ljust(64, "a")
        monkeypatch.setattr("django.template.context_processors.get_token", lambda request: token)
        response = member.get(screen(charge))
        html = response.content.decode()
        assert response.status_code == 200
        assert "90,00" in html and PAY in html
        # Cap camp de targeta ni de contrasenya, ni «CVV» al text visible. No es mira l'HTML
        # sencer: el testimoni CSRF (aleatori) hi surt i pot contenir «cvv».
        fields = re.findall(r"<(?:input|select|textarea)[^>]*>", html)
        fields = [field.lower() for field in fields if "csrfmiddlewaretoken" not in field]
        assert not any('type="password"' in f or "cvv" in f or '"cc-' in f for f in fields)
        assert "cvv" not in re.sub(r"<[^>]+>", " ", html).lower()

    def test_ca_m05b_01_pay_takes_the_browser_to_the_provider_page(self, member, charge):
        response = start(member, charge)

        attempt = Attempt.objects.get()
        assert attempt.status == S.IN_PROGRESS and attempt.amount_cents == 9000
        assert response.status_code == 302
        assert response["Location"] == f"{SITE}{fake.PAY_PATH}{attempt.provider_order_id}/"

    def test_ca_m05b_02_the_ok_return_says_confirming_and_the_charge_does_not_change(
        self, member, charge
    ):
        start(member, charge)
        response = member.get(screen(charge) + "?tornada=ok")

        html = response.content.decode()
        assert CONFIRMING in html and PAY not in html
        charge.refresh_from_db()
        assert charge.status == Charge.Status.PENDING
        assert not Payment.objects.exists()
        assert Attempt.objects.get().status == S.IN_PROGRESS

    def test_the_return_never_says_paid_if_the_server_does_not(self, member, charge):
        start(member, charge)
        finish(Attempt.objects.get(), S.FAILED)
        html = member.get(screen(charge) + "?tornada=ok").content.decode()
        assert "No s'ha completat" in html and PAY in html
        assert "Pagat" not in html

    def test_ca_m05b_08_p83_an_attempt_left_halfway_blocks_a_new_one(self, member, charge):
        """P-83, opció per defecte: el soci torna sense pagar; «Paga» no obre cap altre intent
        ni cap altra ordre, i la pantalla explica que s'espera la confirmació."""
        start(member, charge)
        order = Attempt.objects.get().provider_order_id
        assert len(fake._orders) == 1

        response = start(member, charge)

        assert response.status_code == 302 and response["Location"] == screen(charge)
        assert Attempt.objects.count() == 1 and list(fake._orders) == [order]
        html = member.get(screen(charge)).content.decode()
        assert CONFIRMING in html and "no en pots començar cap altre" in html

    def test_a_paid_charge_is_not_paid_again(self, member, charge):
        Charge.objects.filter(pk=charge.pk).update(status=Charge.Status.PAID)
        assert "Pagat" in member.get(screen(charge)).content.decode()
        assert start(member, charge)["Location"] == screen(charge)
        assert not Attempt.objects.exists()

    def test_if_the_provider_fails_the_member_is_told_and_nothing_is_left(
        self, member, charge, settings
    ):
        settings.PAYMENTS_PROVIDER = ""
        response = start(member, charge)
        assert response["Location"] == screen(charge)
        html = member.get(screen(charge)).content.decode()
        assert "Ara no es pot pagar amb targeta" in html
        assert not Attempt.objects.exists()

    def test_pay_is_only_a_post(self, member, charge):
        assert member.get(reverse("payments:pay_card", args=[charge.pk])).status_code == 405


class TestOnlyTheirOwn:
    """M05b-4, «per objecte»: el càrrec o l'intent d'un altre, i el que no existeix, «no trobat»."""

    @pytest.fixture
    def other_charge(self, make_person):
        return new_charge(make_person("Pau", "Inventat"))

    def test_the_charge_of_someone_else_is_not_found_and_logged(self, member, other_charge):
        assert member.get(screen(other_charge)).status_code == 404
        assert start(member, other_charge).status_code == 404
        assert not Attempt.objects.exists()
        logged = AuditEntry.objects.filter(action=audit.Action.PERSONAL_AREA_NOT_FOUND)
        assert logged.count() == 2
        assert member.get(reverse("payments:charge", args=[999999])).status_code == 404

    def test_the_attempt_of_someone_else_is_not_found(self, member, other_charge):
        owner = Account.objects.create_personal(other_charge.person, "pau@example.org", PASSWORD)
        owner.status = Account.Status.ACTIVE
        owner.save()
        checkout.start_payment(other_charge, "card", owner)
        attempt = Attempt.objects.get()
        url = reverse("payments:attempt_status", args=[attempt.pk])
        assert member.get(url).status_code == 404

    def test_without_a_session_it_goes_to_the_login(self, client, charge):
        response = client.get(screen(charge))
        assert response.status_code == 302 and "/entrar/" in response["Location"]

    def test_an_expired_session_on_the_htmx_poll_reloads_the_page(self, client, charge):
        response = client.get(
            reverse("payments:attempt_status", args=[1]),
            headers={"HX-Request": "true", "HX-Current-URL": "http://testserver" + screen(charge)},
        )
        assert response.status_code == 401 and response["HX-Redirect"]


class TestHtmxStatus:
    def test_while_in_progress_it_asks_again_and_stops_when_it_ends(self, member, charge):
        start(member, charge)
        attempt = Attempt.objects.get()
        url = reverse("payments:attempt_status", args=[attempt.pk])

        html = member.get(url, headers={"HX-Request": "true"}).content.decode()
        assert CONFIRMING in html and 'hx-trigger="every 3s"' in html and url in html

        finish(attempt, S.FAILED)
        html = member.get(url, headers={"HX-Request": "true"}).content.decode()
        assert "hx-trigger" not in html and PAY in html


class TestFakeProviderPage:
    def pay_page(self, member, charge):
        start(member, charge)
        order = Attempt.objects.get().provider_order_id
        return order, reverse("payments:fake_pay", args=[order])

    def test_it_shows_the_amount_and_no_card_field(self, member, charge):
        _order, url = self.pay_page(member, charge)
        html = Client().get(url).content.decode()  # una pàgina de fora: sense sessió
        assert "90,00" in html
        assert not re.search(r'<input[^>]*type="(text|number|tel|password)"', html)

    @pytest.mark.parametrize(
        ("choice", "status", "back"), [("pay", base.PAID, "ok"), ("deny", base.DENIED, "ko")]
    )
    def test_the_result_sends_the_signed_notification_and_returns_the_browser(
        self, member, charge, sent, choice, status, back
    ):
        order, url = self.pay_page(member, charge)

        response = Client().post(url, {"resultat": choice})

        assert sent == [200]
        event = ProviderEvent.objects.get()
        assert (event.order_id, event.event_type, event.amount_cents) == (order, status, 9000)
        assert event.result == ProviderEvent.Result.RECEIVED
        assert response["Location"] == f"{SITE}{screen(charge)}?tornada={back}"
        # La pàgina del proveïdor no toca res de la plataforma: això ho fa el 05b (T-M05b-05).
        charge.refresh_from_db()
        assert charge.status == Charge.Status.PENDING

    def test_leaving_without_paying_sends_nothing(self, member, charge, sent):
        _order, url = self.pay_page(member, charge)
        response = Client().post(url, {"resultat": "leave"})
        assert sent == [] and not ProviderEvent.objects.exists()
        assert response["Location"] == f"{SITE}{screen(charge)}?tornada=ko"
        assert Client().get(url).status_code == 200  # s'hi pot tornar: l'ordre continua oberta

    def test_a_closed_unknown_or_bad_order_is_not_found(self, member, charge, sent):
        _order, url = self.pay_page(member, charge)
        assert Client().post(url, {"resultat": "res"}).status_code == 404
        Client().post(url, {"resultat": "pay"})
        assert Client().get(url).status_code == 404  # ja pagada
        assert Client().get(reverse("payments:fake_pay", args=["fake-no"])).status_code == 404

    def test_only_with_the_fake_provider(self, member, charge, settings):
        _order, url = self.pay_page(member, charge)
        settings.PAYMENTS_PROVIDER = ""
        assert Client().get(url).status_code == 404

    def test_the_return_path_is_the_payment_screen(self, charge):
        assert checkout.RETURN_PATH.format(charge=charge.pk, result="ok") == (
            screen(charge) + "?tornada=ok"
        )
