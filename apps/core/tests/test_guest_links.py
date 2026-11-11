"""Enllaços de convidat (T-M00-02; spec 00, HU-02, CA-02.1 a CA-02.8, RN-30 a RN-33, V-02;
decisió 021). Només dades inventades.

CA-02.9 (pàgina de retorn del formulari de pagament) és del 05b: aquí no hi ha cap pagament.
"""

import logging
import re
import time
from datetime import timedelta

import pytest
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError
from django.http import Http404
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts import limits
from apps.accounts.models import Account, EmailLinkRequest
from apps.accounts.security import AREA_ADMIN
from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY
from apps.core import audit, charges, guest_links, mail
from apps.core.models import (
    AuditEntry,
    Charge,
    Department,
    GuestLink,
    OutgoingEmail,
    Payment,
    Person,
    Role,
)
from conftest import PASSWORD, CommittedDataTestCase, run_together

pytestmark = pytest.mark.django_db
R = Role.Code
MANAGEMENT_ROLES = [code for code in R.values if code not in ("member", "visitor", "guest")]
SYSTEM = audit.system("activities-guest-enrolment")
PAGE = reverse("core:guest")
REQUEST = reverse("core:guest_link_request")
ADMIN_LIST = reverse("administration:guest_links")
EMAIL = "mar@example.org"
INVENTED = "testimoni-inventat-que-no-es-de-cap-enllac"
INVALID = "Aquest enllaç no és vàlid o ha caducat."
LIMITED = "Massa intents seguits"
NOT_YET = "El pagament en línia encara no està disponible"
FAILURES = limits.GUEST_FAILED_WINDOW.max_count


@pytest.fixture
def admin(make_admin):
    return make_admin(R.ADMINISTRATOR)


@pytest.fixture
def courses(admin):
    return charges.create_department("Cursos", by=admin)


@pytest.fixture
def person(make_person):
    return make_person(
        "Mar",
        "Soler",
        contact_email=EMAIL,
        phone="600111222",
        id_document_type="dni",
        id_document_number="12345678Z",
    )


@pytest.fixture
def other(make_person):
    return make_person("Biel", "Ferrer", contact_email="biel@example.org", phone="600333444")


def new_charge(person, by, department, concept="Curs Open Water", amount_cents=12000):
    return charges.create_charge(
        person,
        kind=Charge.Kind.ENROLMENT,
        amount_cents=amount_cents,
        concept=concept,
        origin="activities",
        department=department,
        by=by,
    )


@pytest.fixture
def charge(person, admin, courses):
    return new_charge(person, admin, courses)


def last_token() -> str:
    """El testimoni en clar només existeix dins del correu: es llegeix de l'últim de la cua."""
    body = OutgoingEmail.objects.filter(template=guest_links.EMAIL_TEMPLATE).latest("pk").body_text
    return re.search(r"/convidat/([\w-]+)/", body).group(1)


def send(charge, by):
    """Genera i envia l'enllaç; torna l'enllaç i el testimoni del correu."""
    link = guest_links.create(charge.person, charge, by=by)
    return link, last_token()


def open_link(client, token, **extra):
    first = client.get(reverse("core:guest_link", args=[token]), **extra)
    assert first.status_code == 302
    assert first["Location"] == PAGE
    assert first["Referrer-Policy"] == "no-referrer"
    return client.get(PAGE, **extra)


def main(response) -> str:
    """El contingut de <main>: la resta de la pàgina porta el testimoni CSRF, diferent cada cop."""
    text = re.search(r"<main.*?</main>", response.content.decode(), re.S).group(0)
    return re.sub(r'name="csrfmiddlewaretoken" value="[^"]+"', "", text)


def admin_client(account):
    client = Client()
    client.force_login(account)
    session = client.session
    session[AREA_SESSION_KEY] = AREA_ADMIN
    session[AUTH_AT_SESSION_KEY] = time.time()
    session.save()
    return client


def pay(charge):
    payment = Payment.objects.create(charge=charge, method="card", amount_cents=charge.amount_cents)
    return charges.mark_paid(charge, payment, origin="provider", by=audit.system("proves"))


def expire(link):
    GuestLink.objects.filter(pk=link.pk).update(expires_at=timezone.now() - timedelta(seconds=1))


class TestCa021Generate:
    def test_ca_02_1_sends_the_link_and_stores_only_the_hash(self, admin, person, charge):
        link, token = send(charge, admin)
        email = OutgoingEmail.objects.get()
        assert email.to_address == EMAIL and email.person == person
        assert link.person == person and link.charge == charge and link.created_by == admin
        assert link.purpose == GuestLink.Purpose.PAYMENT
        assert link.token_hash == guest_links._hash(token) != token
        assert len(token) >= 43  # 256 bits en base64 (V-02)
        stored = " ".join(str(v) for v in GuestLink.objects.values().get().values())
        assert token not in stored
        # V-02: 7 dies.
        lifetime = link.expires_at - link.created_at
        assert abs(lifetime - timedelta(days=7)) < timedelta(seconds=5)

    def test_ca_02_1_the_email_carries_no_personal_or_charge_data(self, admin, person, charge):
        send(charge, admin)
        email = OutgoingEmail.objects.get()
        text = email.subject + email.body_text
        for value in ("Mar", "Soler", "Open Water", "120", "12345678Z", "600111222"):
            assert value not in text
        assert "7 dies" in text

    def test_ca_02_1_is_recorded_without_the_token(self, admin, charge):
        link, token = send(charge, admin)
        entry = AuditEntry.objects.get(action=guest_links.CREATED)
        assert entry.actor_account == admin
        assert (entry.target_type, entry.target_id) == ("core.guestlink", str(link.pk))
        assert entry.details == {"charge": charge.pk, "replaces": []}
        row = str(AuditEntry.objects.values().get(pk=entry.pk))
        assert token not in row and link.token_hash not in row

    @pytest.mark.parametrize("role", [r for r in MANAGEMENT_ROLES if r != R.ADMINISTRATOR])
    def test_ca_02_1_other_roles_cannot_generate(self, make_admin, charge, role):
        # M5: a la configuració inicial, només l'administrador.
        with pytest.raises(Http404):
            guest_links.create(charge.person, charge, by=make_admin(role))
        assert not GuestLink.objects.exists() and not OutgoingEmail.objects.exists()

    def test_ca_02_1_a_personal_account_or_nobody_cannot_generate(self, charge, personal_account):
        for by in (personal_account, None, audit.ANONYMOUS):
            with pytest.raises(Http404):
                guest_links.create(charge.person, charge, by=by)
        assert not GuestLink.objects.exists()

    def test_a_module_generates_as_system(self, charge):
        # Contracte per al 02 i el 06: la inscripció d'un convidat no la fa cap compte.
        link = guest_links.create(charge.person, charge, guest_links.PAYMENT, by=SYSTEM)
        assert link.created_by is None
        entry = AuditEntry.objects.get(action=guest_links.CREATED)
        assert entry.actor_kind == "system" and entry.actor_origin == SYSTEM.origin

    def test_only_a_pending_charge_of_that_person(self, admin, person, other, charge, courses):
        with pytest.raises(ValidationError):
            guest_links.create(other, charge, by=admin)
        with pytest.raises(ValidationError):
            guest_links.create(person, person, by=admin)  # només càrrecs, de moment
        with pytest.raises(ValidationError):
            guest_links.create(person, charge, "enrolment", by=admin)
        pay(charge)
        with pytest.raises(ValidationError):
            guest_links.create(person, charge, by=admin)
        cancelled = charges.cancel(new_charge(person, admin, courses), "Error", by=admin)
        with pytest.raises(ValidationError):
            guest_links.create(person, cancelled, by=admin)
        assert not GuestLink.objects.exists() and not OutgoingEmail.objects.exists()

    def test_needs_a_contact_email(self, admin, make_person, courses):
        nobody = make_person("Pau", "Roig")
        with pytest.raises(ValidationError):
            guest_links.create(nobody, new_charge(nobody, admin, courses), by=admin)
        assert not GuestLink.objects.exists()


class TestCa022GuestPage:
    def test_ca_02_2_shows_only_the_linked_charge(self, client, admin, charge, other, courses):
        _, token = send(charge, admin)
        send(
            new_charge(other, admin, courses, concept="Sortida a les Medes", amount_cents=4550),
            admin,
        )
        response = open_link(client, token)
        assert response.status_code == 200
        text = response.content.decode()
        assert "Curs Open Water" in text and "120,00 €" in text and "Pendent" in text
        # Cap dada d'una altra persona.
        for value in ("Medes", "45,50", "Biel", "Ferrer", "biel@example.org"):
            assert value not in text
        # Cap dada personal pròpia (minimització) ni el testimoni.
        for value in ("Mar", "Soler", EMAIL, "600111222", "12345678Z", token):
            assert value not in text
        assert "no-store" in response["Cache-Control"]
        assert "noindex" in response["X-Robots-Tag"]
        assert response["Referrer-Policy"] == "same-origin"

    def test_ca_02_2_no_payment_is_offered_yet(self, client, admin, charge):
        # El pagament és del 05b: cap formulari ni cap botó, només l'avís.
        _, token = send(charge, admin)
        text = main(open_link(client, token))
        assert NOT_YET in text
        assert "<form" not in text and "<button" not in text

    def test_ca_02_2_the_object_comes_from_the_link_never_from_the_address(
        self, client, admin, charge, other, courses
    ):
        _, token = send(charge, admin)
        foreign = new_charge(other, admin, courses, concept="Sortida a les Medes")
        open_link(client, token)
        for query in ({"charge": foreign.pk}, {"pk": foreign.pk}, {"id": foreign.pk}):
            text = client.get(PAGE, query).content.decode()
            assert "Curs Open Water" in text and "Medes" not in text
        assert client.post(PAGE, {"charge": foreign.pk}).status_code == 405

    def test_ca_02_2_without_a_link_there_is_nothing(self, client, admin, charge):
        send(charge, admin)
        response = client.get(PAGE)
        assert INVALID in main(response) and "Open Water" not in main(response)

    def test_contract_resolve_can_pay_and_actor(self, admin, person, charge):
        link, token = send(charge, admin)
        resolved = guest_links.resolve(token)
        assert resolved == link and resolved.charge == charge and resolved.person == person
        assert guest_links.can_pay(resolved)
        actor = guest_links.actor(resolved)
        assert actor.kind == "guest" and actor.person == person
        assert actor.origin == f"guest_link:{link.pk}"  # CA-14.6: mai el testimoni
        assert guest_links.resolve(INVENTED) is None and guest_links.resolve("") is None

    def test_contract_for_request_gives_the_link_of_this_browser(self, client, rf, admin, charge):
        link, token = send(charge, admin)
        open_link(client, token)
        request = rf.get(PAGE)
        request.session = client.session
        assert guest_links.for_request(request) == link
        request.session = Client().session
        assert guest_links.for_request(request) is None


class TestCa023NotValid:
    def responses(self, admin, charge, courses):
        """Un enllaç caducat, un de revocat, un de substituït, un d'un càrrec anul·lat, un d'una
        persona anonimitzada i un testimoni inventat."""
        tokens = {"unknown": INVENTED}
        link, tokens["expired"] = send(charge, admin)
        expire(link)
        person = charge.person
        link, tokens["revoked"] = send(new_charge(person, admin, courses), admin)
        assert guest_links.revoke(link, by=admin)
        _, tokens["replaced"] = send(new_charge(person, admin, courses), admin)
        guest_links.resend(GuestLink.objects.latest("pk"), by=admin)
        cancelled = new_charge(person, admin, courses)
        _, tokens["cancelled"] = send(cancelled, admin)
        charges.cancel(cancelled, "Inscripció anul·lada", by=admin)
        gone = Person.objects.create(
            first_name="Ona", origin="web", contact_email="ona@example.org"
        )
        _, tokens["anonymised"] = send(new_charge(gone, admin, courses), admin)
        Person.objects.filter(pk=gone.pk).update(status="anonymised", anonymous_ref="anon-1")
        return {name: open_link(Client(), token) for name, token in tokens.items()}

    def test_ca_02_3_no_data_and_offers_a_new_link(self, admin, charge, courses):
        responses = self.responses(admin, charge, courses)
        bodies = {name: main(response) for name, response in responses.items()}
        assert len(set(bodies.values())) == 1  # no es pot saber per què no funciona
        text = bodies["expired"]
        assert INVALID in text and REQUEST in text and "Demana un enllaç nou" in text
        for value in ("Open Water", "120,00", "Mar", "Soler", "Pendent"):
            assert value not in text
        assert {response.status_code for response in responses.values()} == {200}

    def test_ca_02_3_a_link_revoked_while_open_stops_at_once(self, client, admin, charge):
        link, token = send(charge, admin)
        assert "Open Water" in main(open_link(client, token))
        guest_links.revoke(link, by=admin)
        assert INVALID in main(client.get(PAGE)) and "Open Water" not in main(client.get(PAGE))
        assert guest_links.SESSION_KEY not in client.session

    def test_revoking_needs_m5_and_is_recorded(self, admin, make_admin, charge, personal_account):
        link, token = send(charge, admin)
        for by in (make_admin(R.TREASURER), make_admin(R.SECRETARY), personal_account, None):
            with pytest.raises(Http404):
                guest_links.revoke(link, by=by)
        assert guest_links.resolve(token) == link
        assert guest_links.revoke(link, by=admin) is True
        assert guest_links.revoke(link, by=admin) is False  # ja ho estava
        entry = AuditEntry.objects.get(action=guest_links.REVOKED)
        assert entry.actor_account == admin and entry.target_id == str(link.pk)
        charge.refresh_from_db()
        assert charge.status == Charge.Status.PENDING  # L10: el càrrec no canvia


class TestCa024PaidCharge:
    def test_ca_02_4_a_paid_charge_only_shows_its_state(self, client, admin, charge):
        link, token = send(charge, admin)
        pay(charge)
        text = main(open_link(client, token))
        assert "Open Water" in text and "Pagat" in text and "Pendent" not in text
        assert NOT_YET not in text and "<form" not in text and "<button" not in text
        resolved = guest_links.resolve(token)
        assert resolved == link and not guest_links.can_pay(resolved)

    def test_ca_02_4_until_the_link_expires(self, client, admin, charge):
        link, token = send(charge, admin)
        pay(charge)
        expire(link)
        assert INVALID in main(open_link(client, token))
        assert guest_links.resolve(token) is None


class TestCa025Resend:
    def test_ca_02_5_the_previous_link_stops_working(self, admin, charge):
        old, old_token = send(charge, admin)
        new = guest_links.resend(old, by=admin)
        new_token = last_token()
        old.refresh_from_db()
        assert old.replaced_by == new and new.replaced_by is None
        assert guest_links.resolve(old_token) is None
        assert guest_links.resolve(new_token) == new
        assert INVALID in main(open_link(Client(), old_token))
        assert "Open Water" in main(open_link(Client(), new_token))
        assert OutgoingEmail.objects.count() == 2
        entry = AuditEntry.objects.filter(action=guest_links.CREATED).latest("pk")
        assert entry.details == {"charge": charge.pk, "replaces": [old.pk]}

    def test_ca_02_5_an_open_page_with_the_old_link_stops_too(self, client, admin, charge):
        old, old_token = send(charge, admin)
        open_link(client, old_token)
        guest_links.resend(old, by=admin)
        assert INVALID in main(client.get(PAGE))

    def test_ca_02_5_generating_again_is_resending(self, admin, charge):
        _, first = send(charge, admin)
        _, second = send(charge, admin)
        _, third = send(charge, admin)
        assert [guest_links.resolve(t) is not None for t in (first, second, third)] == [
            False,
            False,
            True,
        ]
        assert GuestLink.objects.filter(replaced_by__isnull=True).count() == 1

    def test_ca_02_5_resending_needs_m5(self, admin, make_admin, charge):
        link, token = send(charge, admin)
        with pytest.raises(Http404):
            guest_links.resend(link, by=make_admin(R.TREASURER))
        assert guest_links.resolve(token) == link


class TestCa026RequestNew:
    def ask(self, email, client=None, **extra):
        return (client or Client()).post(REQUEST, {"email": email}, **extra)

    def test_ca_02_6_same_response_whether_the_address_exists_or_not(self, admin, charge):
        old, old_token = send(charge, admin)
        known = self.ask(EMAIL)
        unknown = self.ask("ningu@example.org")
        assert known.status_code == unknown.status_code == 200
        assert main(known) == main(unknown)
        assert "Si aquesta adreça té cap pagament pendent" in main(known)
        # Amb l'adreça coneguda sí que hi ha un enllaç nou, i l'anterior deixa de funcionar.
        assert OutgoingEmail.objects.count() == 2
        new_token = last_token()
        assert new_token != old_token and new_token not in known.content.decode()
        assert guest_links.resolve(old_token) is None
        new = guest_links.resolve(new_token)
        assert new.charge == charge and new.created_by is None
        entry = AuditEntry.objects.filter(action=guest_links.CREATED).latest("pk")
        assert entry.actor_kind == "system" and entry.details["replaces"] == [old.pk]

    def test_ca_02_6_the_address_is_normalised_and_an_expired_link_is_renewed(self, admin, charge):
        link, _ = send(charge, admin)
        expire(link)
        self.ask("  MAR@Example.org ")
        assert guest_links.resolve(last_token()).charge == charge

    def test_ca_02_6_nothing_is_sent_without_a_renewable_link(self, admin, person, charge, courses):
        # Sense cap enllaç previ, amb l'enllaç revocat o amb el càrrec pagat o anul·lat.
        revoked, _ = send(new_charge(person, admin, courses), admin)
        guest_links.revoke(revoked, by=admin)
        paid = new_charge(person, admin, courses)
        send(paid, admin)
        pay(paid)
        cancelled = new_charge(person, admin, courses)
        send(cancelled, admin)
        charges.cancel(cancelled, "Error", by=admin)
        before = OutgoingEmail.objects.count()
        response = self.ask(EMAIL)
        assert OutgoingEmail.objects.count() == before
        assert main(response) == main(self.ask("ningu@example.org"))

    def test_ca_02_6_limited_by_recipient_with_the_same_response(self, admin, charge):
        send(charge, admin)
        allowed = limits.RECIPIENT_WINDOWS[0].max_count
        responses = [self.ask(EMAIL, REMOTE_ADDR=f"198.51.100.{i}") for i in range(allowed + 1)]
        assert OutgoingEmail.objects.count() == 1 + allowed
        assert len({main(response) for response in responses}) == 1
        entry = AuditEntry.objects.get(action=guest_links.REQUEST_LIMITED)
        assert entry.details == {"scope": "recipient"}

    def test_ca_02_6_limited_by_origin_with_the_same_response(self, admin, charge):
        send(charge, admin)
        allowed = limits.ORIGIN_WINDOW.max_count
        for _ in range(allowed):
            self.ask("ningu@example.org")
        response = self.ask(EMAIL)
        assert OutgoingEmail.objects.count() == 1
        assert main(response) == main(self.ask("ningu@example.org", REMOTE_ADDR="198.51.100.9"))
        assert EmailLinkRequest.objects.filter(purpose=limits.GUEST_NEW).count() == allowed + 1
        # Comptador propi: no frena els enllaços del compte personal ni al revés.
        assert not limits.origin_limited("127.0.0.1")

    def test_ca_02_6_the_form_is_public_and_needs_a_valid_address(self, client):
        assert "Correu electrònic" in main(client.get(REQUEST))
        response = self.ask("no-es-cap-correu", client)
        assert "Si aquesta adreça" not in main(response)
        assert not EmailLinkRequest.objects.exists()


class TestCa027Attempts:
    def fail(self, client, times, token=INVENTED, **extra):
        for _ in range(times):
            assert client.get(reverse("core:guest_link", args=[token]), **extra).status_code == 302

    def test_ca_02_7_blocked_after_the_failed_attempts_of_v02(self, client, admin, charge):
        _, token = send(charge, admin)
        self.fail(client, FAILURES)
        response = client.get(reverse("core:guest_link", args=[token]))
        assert response.status_code == 429
        text = main(response)
        assert LIMITED in text and "Open Water" not in text and INVALID not in text
        assert response["Referrer-Policy"] == "no-referrer"
        # Bloquejat, no s'ha arribat a mirar el testimoni: la pàgina tampoc no mostra res.
        assert INVALID in main(client.get(PAGE))

    def test_ca_02_7_a_dead_link_counts_like_an_unknown_token(self, client, admin, charge):
        link, token = send(charge, admin)
        expire(link)
        self.fail(client, FAILURES, token)
        assert client.get(reverse("core:guest_link", args=[INVENTED])).status_code == 429

    def test_ca_02_7_valid_links_do_not_count(self, client, admin, charge):
        _, token = send(charge, admin)
        for _ in range(FAILURES + 2):
            assert "Open Water" in main(open_link(client, token))
        assert not EmailLinkRequest.objects.exists()

    def test_ca_02_7_is_per_origin(self, client, admin, charge):
        _, token = send(charge, admin)
        self.fail(client, FAILURES)
        assert client.get(reverse("core:guest_link", args=[token])).status_code == 429
        assert "Open Water" in main(open_link(Client(), token, REMOTE_ADDR="198.51.100.7"))

    def test_ca_02_7_blocked_attempts_do_not_count_and_the_block_ends(self, client, admin, charge):
        _, token = send(charge, admin)
        self.fail(client, FAILURES)
        for _ in range(5):
            assert client.get(reverse("core:guest_link", args=[INVENTED])).status_code == 429
        rows = EmailLinkRequest.objects.filter(purpose=limits.GUEST_FAILED)
        assert rows.count() == FAILURES
        assert AuditEntry.objects.filter(action=guest_links.ORIGIN_BLOCKED).count() == 1
        past = timezone.now() - limits.GUEST_FAILED_COOLDOWN - timedelta(seconds=1)
        rows.update(created_at=past)
        assert "Open Water" in main(open_link(client, token))

    def test_ca_02_7_separate_from_the_other_limits(self, client):
        self.fail(client, FAILURES)
        assert not limits.origin_limited("127.0.0.1")
        assert limits.start_card_verification("127.0.0.1")
        assert limits.start_guest_link_request("127.0.0.1") is not None


class TestCa028TokenIsNeverLogged:
    def test_ca_02_8_not_in_logs_audit_session_or_tables(self, client, admin, charge, caplog):
        link, token = send(charge, admin)
        email = OutgoingEmail.objects.get()
        caplog.set_level(logging.DEBUG)
        url = reverse("core:guest_link", args=[token])
        open_link(client, token)
        assert client.post(url).status_code == 405
        assert client.get(reverse("core:guest_link", args=[INVENTED])).status_code == 302
        for _ in range(FAILURES):
            client.get(reverse("core:guest_link", args=[INVENTED]))
        assert client.get(url).status_code == 429
        guest_links.revoke(link, by=admin)
        assert token not in caplog.text and INVENTED not in caplog.text
        # El testimoni només és al cos del correu mentre espera a la cua (RN-32).
        for model in (AuditEntry, EmailLinkRequest, GuestLink, Session):
            stored = " ".join(str(v) for row in model.objects.values() for v in row.values())
            assert token not in stored and INVENTED not in stored
        for session in Session.objects.all():
            assert token not in str(session.get_decoded())
        mail.deliver(email.pk)
        sent = " ".join(str(v) for v in OutgoingEmail.objects.values().get(pk=email.pk).values())
        assert token not in sent

    def test_ca_02_8_the_session_keeps_only_the_internal_id(self, client, admin, charge):
        link, token = send(charge, admin)
        open_link(client, token)
        assert client.session[guest_links.SESSION_KEY] == link.pk

    def test_ca_02_8_other_methods_are_not_allowed_and_do_not_count(self, client):
        response = client.post(reverse("core:guest_link", args=[INVENTED]))
        assert response.status_code == 405
        assert not EmailLinkRequest.objects.exists()


class TestAdminScreen:
    """Pantalla d'administració: M5 al servidor a les tres rutes."""

    def routes(self, charge):
        return [
            ("get", ADMIN_LIST),
            ("post", reverse("administration:guest_link_send", args=[charge.pk])),
            ("post", reverse("administration:guest_link_revoke", args=[charge.pk])),
        ]

    @pytest.mark.parametrize("role", MANAGEMENT_ROLES)
    def test_only_m5_reaches_the_three_routes(self, make_admin, admin, charge, role):
        send(charge, admin)
        client = admin_client(make_admin(role))
        allowed = role == R.ADMINISTRATOR
        for method, url in self.routes(charge):
            status = getattr(client, method)(url).status_code
            assert status == ({"get": 200, "post": 303}[method] if allowed else 404), url
        if not allowed:
            assert GuestLink.objects.filter(revoked_at__isnull=True).count() == 1
            assert OutgoingEmail.objects.count() == 1

    def test_a_personal_session_does_not_reach_them(
        self, client, login_as, personal_account, charge
    ):
        login_as(personal_account, "personal")
        for method, url in self.routes(charge):
            response = getattr(client, method)(url)
            assert response.status_code == 302
            assert response["Location"].startswith(reverse("administration:login"))
        assert not GuestLink.objects.exists()

    def test_lists_pending_charges_of_people_without_account(
        self, admin, person, other, charge, courses
    ):
        account = Account.objects.create_personal(other, "biel@example.org", PASSWORD)
        assert account.kind == Account.Kind.PERSONAL
        new_charge(other, admin, courses, concept="Sortida a les Medes")
        cancelled = new_charge(person, admin, courses, concept="Bateig de mar")
        charges.cancel(cancelled, "Error", by=admin)
        response = admin_client(admin).get(ADMIN_LIST)
        text = main(response)
        assert "Mar Soler" in text and "Curs Open Water" in text and "120,00" in text
        assert "Genera i envia" in text and "Revoca" not in text
        for value in ("Medes", "Biel", "Bateig", EMAIL):
            assert value not in text

    def test_generate_resend_and_revoke_from_the_screen(self, admin, charge):
        client = admin_client(admin)
        send_url = reverse("administration:guest_link_send", args=[charge.pk])
        response = client.post(send_url)
        assert response.status_code == 303 and response["Location"] == ADMIN_LIST
        first = last_token()
        text = main(client.get(ADMIN_LIST))
        assert "Enllaç enviat" in text and "Vigent fins al" in text
        assert "Reenvia<span" in text and "Revoca l'enllaç" in text
        assert first not in text and GuestLink.objects.get().token_hash not in text
        client.post(send_url)
        assert guest_links.resolve(first) is None
        second = last_token()
        assert guest_links.resolve(second).created_by == admin
        client.post(reverse("administration:guest_link_revoke", args=[charge.pk]))
        assert guest_links.resolve(second) is None
        text = main(client.get(ADMIN_LIST))
        assert "Enllaç revocat" in text and "Revocat" in text and "Vigent" not in text
        actions = list(AuditEntry.objects.order_by("pk").values_list("action", flat=True))
        assert actions[-3:] == [guest_links.CREATED, guest_links.CREATED, guest_links.REVOKED]

    def test_a_paid_charge_stays_while_its_link_works_and_can_be_revoked(self, admin, charge):
        link, token = send(charge, admin)
        pay(charge)
        client = admin_client(admin)
        text = main(client.get(ADMIN_LIST))
        assert "Pagat" in text and "Revoca" in text and "Reenvia<span" not in text
        # El servei rebutja un enllaç nou per a un càrrec pagat, encara que es demani a mà.
        client.post(reverse("administration:guest_link_send", args=[charge.pk]))
        assert OutgoingEmail.objects.count() == 1 and guest_links.resolve(token) == link
        assert "Només es pot enviar un enllaç d&#x27;un càrrec pendent" in main(
            client.get(ADMIN_LIST)
        )
        client.post(reverse("administration:guest_link_revoke", args=[charge.pk]))
        assert guest_links.resolve(token) is None
        assert "Open Water" not in main(client.get(ADMIN_LIST))

    def test_charges_outside_the_screen_are_not_found(self, admin, person, other, courses):
        Account.objects.create_personal(other, "biel@example.org", PASSWORD)
        with_account = new_charge(other, admin, courses)
        cancelled = charges.cancel(new_charge(person, admin, courses), "Error", by=admin)
        client = admin_client(admin)
        for pk in (with_account.pk, cancelled.pk, 999_999):
            for name in ("guest_link_send", "guest_link_revoke"):
                assert client.post(reverse(f"administration:{name}", args=[pk])).status_code == 404
        assert not GuestLink.objects.exists()

    def test_revoking_without_a_link_says_so(self, admin, charge):
        client = admin_client(admin)
        client.post(reverse("administration:guest_link_revoke", args=[charge.pk]))
        assert "no té cap enllaç per revocar" in main(client.get(ADMIN_LIST))

    def test_actions_only_with_post(self, admin, charge):
        client = admin_client(admin)
        for name in ("guest_link_send", "guest_link_revoke"):
            assert (
                client.get(reverse(f"administration:{name}", args=[charge.pk])).status_code == 405
            )
        assert not GuestLink.objects.exists()

    def test_a_person_without_email_cannot_be_sent_a_link(self, admin, make_person, courses):
        nobody = make_person("Pau", "Roig")
        charge = new_charge(nobody, admin, courses)
        client = admin_client(admin)
        assert "Sense correu de contacte" in main(client.get(ADMIN_LIST))
        client.post(reverse("administration:guest_link_send", args=[charge.pk]))
        assert "no té cap correu de contacte" in main(client.get(ADMIN_LIST))
        assert not GuestLink.objects.exists()

    def test_the_home_link_only_with_m5(self, admin, make_admin):
        home = reverse("administration:home")
        assert ADMIN_LIST in admin_client(admin).get(home).content.decode()
        assert ADMIN_LIST not in admin_client(make_admin(R.TREASURER)).get(home).content.decode()


class TestConcurrentSends(CommittedDataTestCase):
    """Amb PostgreSQL real i una connexió per fil (vegeu `conftest.py`)."""

    def test_ca_02_5_sends_at_once_leave_a_single_working_link(self):
        person = Person.objects.create(first_name="Mar", origin="web", contact_email=EMAIL)
        charge = new_charge(person, SYSTEM, Department.objects.create(name="Cursos"))
        run_together([lambda: guest_links.create(person, charge, by=SYSTEM)] * 4)
        links = GuestLink.objects.filter(charge=charge)
        assert links.count() == 4
        assert links.filter(replaced_by__isnull=True).count() == 1
        tokens = [
            re.search(r"/convidat/([\w-]+)/", body).group(1)
            for body in OutgoingEmail.objects.values_list("body_text", flat=True)
        ]
        assert [guest_links.resolve(token) is not None for token in tokens].count(True) == 1
