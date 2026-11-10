"""Àrea del soci, parts que desbloqueja la 074 (T-M01-16): consentiments opcionals des del perfil
(Q-031 de la 072; RN-M01-78) i canvi del correu d'entrada (RN-M01-79, CA-M01-78) amb els límits de
RN-M01-58. Només dades inventades.
"""

import re
import time
from datetime import date

import pytest
from django.core import signing
from django.test import Client
from django.urls import reverse

from apps.accounts import limits, tokens
from apps.accounts.models import Account, EmailLinkRequest
from apps.accounts.security import AREA_PERSONAL
from apps.accounts.sessions import AREA_SESSION_KEY
from apps.core import audit, consents, crypto
from apps.core.models import AuditEntry, Consent, OutgoingEmail, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.join import PROVISIONAL_OPTIONAL_TEXTS
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

PROFILE = "members:profile"
CONSENT = "members:consent"
CHANGE = "members:change_email"
CONFIRM = "accounts:change_email"
OLD = "anna.soci@example.org"
NEW = "anna.nova@example.org"
CHANGE_TEMPLATE = "canvi-correu"
NOTICE_TEMPLATE = "avis-canvi-correu"


def make_account(email, first="Anna", **fields):
    person = Person.objects.create(
        first_name=first, last_name="Prova", origin=Person.Origin.WEB, **fields
    )
    account = Account.objects.create_personal(person, email, PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    return account


@pytest.fixture
def anna(db):
    return make_account(OLD, contact_email=OLD)


@pytest.fixture
def texts(make_admin):  # noqa: F811
    """Textos PROVISIONALS del butlletí i de les imatges (T-M01-41), només a les proves."""
    publisher = make_admin("administrator")
    return {
        kind: consents.publish_text(kind, content, by=publisher)
        for kind, content in PROVISIONAL_OPTIONAL_TEXTS.items()
    }


@pytest.fixture
def as_anna(login_as, anna):
    return login_as(anna, AREA_PERSONAL)


def rows(person, kind=None):
    found = Consent.objects.filter(person=person).order_by("created_at", "id")
    return found.filter(legal_text__kind=kind) if kind else found


def emails(template, to=None):
    found = OutgoingEmail.objects.filter(template=template)
    return found.filter(to_address=to) if to else found


def link_in(email) -> str:
    return re.search(r"https?://\S+", email.body_text).group(0)


def path_of(link: str) -> str:
    return "/" + link.split("://", 1)[1].split("/", 1)[1]


def messages_of(response):
    return [str(message) for message in response.context["messages"]]


def ask_change(client, email, ip="10.7.0.1"):
    return client.post(reverse(CHANGE), {"new_email": email}, REMOTE_ADDR=ip)


def open_and_confirm(link, client=None):
    client = client or Client()
    client.get(path_of(link))
    page = client.get(reverse(CONFIRM))
    return page, client.post(reverse(CONFIRM))


# --- Consentiments opcionals (Q-031) ------------------------------------------------------------


class TestOptionalConsents:
    def test_no_option_without_a_published_text(self, as_anna, anna):
        """Q-031: com a l'alta, sense text vigent no surt l'opció i el servidor la rebutja."""
        page = as_anna.get(reverse(PROFILE))
        assert page.context["optional_consents"] == []
        assert reverse(CONSENT) not in page.content.decode()
        response = as_anna.post(reverse(CONSENT), {"kind": "newsletter", "action": "grant"})
        assert response.status_code == 404
        assert not rows(anna.person).exists()

    def test_each_published_kind_is_offered_with_its_text(self, as_anna, texts):
        page = as_anna.get(reverse(PROFILE))
        offered = {
            kind: (consent, text) for kind, _, consent, text in page.context["optional_consents"]
        }
        assert offered == {
            "newsletter": (None, texts["newsletter"]),
            "images": (None, texts["images"]),
        }
        body = page.content.decode()
        assert body.count('name="action" value="grant"') == 2
        assert "TEXT PROVISIONAL" in body

    def test_grant_creates_a_web_consent_with_the_current_text_and_audit(
        self, as_anna, anna, texts
    ):
        """Q-031: donar crea una fila nova, canal web, registrada pel compte, i va al registre."""
        response = as_anna.post(reverse(CONSENT), {"kind": "newsletter", "action": "grant"})
        assert response.status_code == 302
        consent = rows(anna.person).get()
        assert (consent.legal_text, consent.action, consent.channel, consent.recorded_by) == (
            texts["newsletter"],
            Consent.Action.GRANTED,
            Consent.Channel.WEB,
            anna,
        )
        assert consent.given_by == Consent.GivenBy.PERSON
        entry = AuditEntry.objects.get(action=consents.GRANTED)
        assert (entry.actor_account, entry.field, entry.old_value, entry.new_value) == (
            anna,
            "consent:newsletter",
            None,
            "granted",
        )
        assert not rows(anna.person, "images").exists()  # cadascun per separat

    def test_withdraw_adds_a_row_and_keeps_the_previous_one(self, as_anna, anna, texts):
        """Q-031 i CA-17.3: retirar afegeix una fila i l'anterior no canvia. El perfil mostra
        l'últim estat."""
        as_anna.post(reverse(CONSENT), {"kind": "images", "action": "grant"})
        as_anna.post(reverse(CONSENT), {"kind": "images", "action": "withdraw"})
        granted, withdrawn = rows(anna.person, "images")
        assert (granted.action, withdrawn.action) == ("granted", "withdrawn")
        assert withdrawn.recorded_by == anna and withdrawn.channel == Consent.Channel.WEB
        entry = AuditEntry.objects.get(action=consents.WITHDRAWN)
        assert (entry.old_value, entry.new_value) == ("granted", "withdrawn")
        page = as_anna.get(reverse(PROFILE))
        latest = {kind: consent for kind, _, consent, _ in page.context["optional_consents"]}
        assert latest["images"] == withdrawn and latest["newsletter"] is None
        assert 'name="action" value="grant"' in page.content.decode()

    def test_repeating_the_same_action_changes_nothing(self, as_anna, anna, texts):
        as_anna.post(reverse(CONSENT), {"kind": "newsletter", "action": "grant"}, follow=True)
        again = as_anna.post(
            reverse(CONSENT), {"kind": "newsletter", "action": "grant"}, follow=True
        )
        assert rows(anna.person).count() == 1
        assert messages_of(again) == ["No has canviat cap consentiment."]
        as_anna.post(reverse(CONSENT), {"kind": "images", "action": "withdraw"})
        assert not rows(anna.person, "images").exists()

    @pytest.mark.parametrize(
        "data",
        [
            {"kind": "privacy", "action": "withdraw"},  # obligatori: no es retira des del perfil
            {"kind": "membership_terms", "action": "grant"},
            {"kind": "inventat", "action": "grant"},
            {"kind": "newsletter", "action": "esborra"},
            {"kind": "newsletter"},
            {},
        ],
    )
    def test_unknown_kind_or_action_is_rejected_without_changes(self, as_anna, anna, texts, data):
        """Abast al servidor: només els tipus opcionals amb text i les dues accions."""
        response = as_anna.post(reverse(CONSENT), data)
        assert response.status_code == 404
        assert not Consent.objects.exists()
        assert not AuditEntry.objects.filter(action__startswith="consents.").exists()

    def test_another_person_id_in_the_form_is_ignored(self, as_anna, anna, texts):
        """Abast d'objecte: la persona surt de la sessió; un identificador manipulat no compta."""
        other = make_account("sentinella@example.org", first="Sentinella")
        as_anna.post(
            reverse(CONSENT),
            {
                "kind": "newsletter",
                "action": "grant",
                "person": other.person.pk,
                "person_id": other.person.pk,
            },
        )
        assert not rows(other.person).exists()
        assert rows(anna.person).count() == 1

    def test_needs_a_personal_session_and_post(self, client, anna, texts):
        response = client.post(reverse(CONSENT), {"kind": "newsletter", "action": "grant"})
        assert response.status_code == 302
        assert response["Location"].startswith(reverse("accounts:login"))
        assert not Consent.objects.exists()

    def test_get_is_not_allowed(self, as_anna, texts):
        assert as_anna.get(reverse(CONSENT)).status_code == 405

    def test_needs_csrf(self, anna, texts):
        client = Client(enforce_csrf_checks=True)
        client.force_login(anna)
        session = client.session
        session[AREA_SESSION_KEY] = AREA_PERSONAL
        session.save()
        client.post(reverse(CONSENT), {"kind": "newsletter", "action": "grant"})
        assert not Consent.objects.exists()

    def test_a_minor_from_14_to_17_changes_them_herself(self, login_as, texts):
        """RN-M01-78 [A validar: assessor, Q-016]: el dona la mateixa persona."""
        today = date.today()
        teen = make_account(
            "menor@example.org", first="Menor", birth_date=date(today.year - 15, 1, 1)
        )
        login_as(teen, AREA_PERSONAL).post(reverse(CONSENT), {"kind": "images", "action": "grant"})
        assert rows(teen.person).get().given_by == Consent.GivenBy.PERSON


# --- Canvi del correu d'entrada (RN-M01-79, CA-M01-78) ------------------------------------------


class TestChangeEmail:
    def test_ca_m01_78_full_flow(self, as_anna, anna):
        """CA-M01-78: enllaç a l'adreça nova, el correu d'entrada no canvia fins que es confirma i
        l'adreça antiga rep un avís sense enllaços."""
        response = ask_change(as_anna, "  Anna.Nova@Example.org ")
        assert response.status_code == 302 and response["Location"] == reverse(PROFILE)
        email = emails(CHANGE_TEMPLATE).get()
        assert email.to_address == NEW
        anna.refresh_from_db()
        assert anna.login == OLD

        page, done = open_and_confirm(link_in(email))
        assert page.context["state"] == "ready" and page.context["new_email"] == NEW
        assert done.context["state"] == "done"
        anna.refresh_from_db()
        anna.person.refresh_from_db()
        assert anna.login == NEW
        assert anna.person.contact_email == NEW

        notice = emails(NOTICE_TEMPLATE).get()
        assert notice.to_address == OLD
        assert "http" not in notice.body_text and NEW not in notice.body_text

    def test_opening_the_link_changes_nothing(self, as_anna, anna):
        """RN-M01-79: només el POST de la confirmació canvia el correu (obrir l'enllaç, no)."""
        ask_change(as_anna, NEW)
        client = Client()
        client.get(path_of(link_in(emails(CHANGE_TEMPLATE).get())))
        client.get(reverse(CONFIRM))
        anna.refresh_from_db()
        assert anna.login == OLD
        assert not emails(NOTICE_TEMPLATE).exists()

    def test_the_link_does_not_show_the_new_address(self, as_anna):
        """L'adreça nova va xifrada dins del testimoni: no queda llegible a l'adreça de l'enllaç."""
        ask_change(as_anna, NEW)
        link = link_in(emails(CHANGE_TEMPLATE).get())
        assert "anna.nova" not in link
        payload = signing.loads(link.rstrip("/").rsplit("/", 1)[1], salt=tokens.CHANGE_EMAIL.salt)
        assert NEW not in str(payload)

    def test_the_old_login_stops_working_and_the_new_one_works(self, as_anna, anna):
        ask_change(as_anna, NEW)
        open_and_confirm(link_in(emails(CHANGE_TEMPLATE).get()))
        login = reverse("accounts:login")
        assert Client().post(login, {"login": OLD, "password": PASSWORD}).status_code == 200
        assert Client().post(login, {"login": NEW, "password": PASSWORD}).status_code == 302

    def test_audit_keeps_the_previous_value(self, as_anna, anna):
        """Registre d'activitat amb el valor anterior del correu d'entrada i del contacte."""
        ask_change(as_anna, NEW)
        open_and_confirm(link_in(emails(CHANGE_TEMPLATE).get()))
        entry = AuditEntry.objects.get(action=audit.Action.LOGIN_EMAIL_CHANGED)
        assert (entry.actor_account, entry.field, entry.old_value, entry.new_value) == (
            anna,
            "login",
            OLD,
            NEW,
        )
        contact = AuditEntry.objects.get(action="persons.updated", field="contact_email")
        assert (contact.old_value, contact.new_value) == (OLD, NEW)
        sent = AuditEntry.objects.get(action=audit.Action.EMAIL_LINK_SENT)
        assert sent.details == {"purpose": "email"}

    def test_a_different_contact_email_is_kept(self, login_as):
        account = make_account(OLD, contact_email="contacte@example.org")
        client = login_as(account, AREA_PERSONAL)
        ask_change(client, NEW)
        open_and_confirm(link_in(emails(CHANGE_TEMPLATE).get()))
        account.person.refresh_from_db()
        assert account.person.contact_email == "contacte@example.org"
        assert not AuditEntry.objects.filter(field="contact_email").exists()

    def test_same_answer_when_the_address_already_has_an_account(
        self, as_anna, anna, admin_account
    ):
        """CA-M01-78 i RN-M01-79: la resposta no revela si l'adreça ja té compte; no s'envia res."""
        make_account("presa@example.org", first="Presa")
        answers, texts = [], set()
        for i, email in enumerate(["lliure@example.org", "presa@example.org", OLD]):
            answers.append(ask_change(as_anna, email, ip=f"10.7.1.{i}"))
            texts.add(tuple(messages_of(as_anna.get(answers[-1]["Location"]))))
        assert len({(r.status_code, r["Location"]) for r in answers}) == 1
        assert len(texts) == 1 and len(next(iter(texts))) == 1
        assert list(emails(CHANGE_TEMPLATE).values_list("to_address", flat=True)) == [
            "lliure@example.org"
        ]

    def test_recipient_limit_same_answer_and_counts_for_origin(self, as_anna):
        """RN-M01-58: com a màxim 3 per hora i destinatari; la limitada respon igual, no envia res
        i compta per a l'origen."""
        per_hour = limits.RECIPIENT_WINDOWS[0].max_count
        answers = [ask_change(as_anna, NEW, ip=f"10.7.2.{i}") for i in range(per_hour + 1)]
        assert emails(CHANGE_TEMPLATE).count() == per_hour
        assert len({r["Location"] for r in answers}) == 1
        assert EmailLinkRequest.objects.filter(purpose="email").count() == per_hour + 1
        limited = AuditEntry.objects.get(action=audit.Action.EMAIL_LINK_LIMITED)
        assert limited.details == {"purpose": "email", "scope": "recipient"}

    def test_origin_limit_same_answer_and_joint_with_recovery(self, as_anna, anna):
        """RN-M01-58: límit d'origen conjunt (10 en 15 minuts) amb la recuperació i el reenviament,
        amb els mateixos valors de `limits.py`."""
        ip = "10.7.3.1"
        reset = reverse("accounts:password_reset_request")
        for i in range(limits.ORIGIN_WINDOW.max_count):
            Client(REMOTE_ADDR=ip).post(reset, {"email": f"ningu{i}@example.org"})
        response = ask_change(as_anna, NEW, ip=ip)
        assert response["Location"] == reverse(PROFILE)
        assert not emails(CHANGE_TEMPLATE).exists()
        assert not EmailLinkRequest.objects.filter(purpose="email").exists()
        limited = AuditEntry.objects.get(action=audit.Action.EMAIL_LINK_LIMITED)
        assert limited.details == {"purpose": "email", "scope": "origin"}

    def test_the_link_is_single_use(self, as_anna, anna):
        ask_change(as_anna, NEW)
        link = link_in(emails(CHANGE_TEMPLATE).get())
        open_and_confirm(link)
        page, again = open_and_confirm(link)
        assert page.context["state"] == "invalid" and again.context["state"] == "invalid"
        assert emails(NOTICE_TEMPLATE).count() == 1
        assert AuditEntry.objects.filter(action=audit.Action.LOGIN_EMAIL_CHANGED).count() == 1

    def test_an_expired_link_changes_nothing(self, monkeypatch, anna):
        hours = tokens.CHANGE_EMAIL.max_age.total_seconds() / 3600
        past = time.time() - (hours + 0.1) * 3600
        with monkeypatch.context() as patch:
            patch.setattr(signing.time, "time", lambda: past)
            token = tokens.make_token(anna, tokens.CHANGE_EMAIL, e=crypto.encrypt(NEW))
        client = Client()
        client.get(reverse("accounts:change_email_link", args=[token]))
        assert client.get(reverse(CONFIRM)).context["state"] == "invalid"
        assert client.post(reverse(CONFIRM)).context["state"] == "invalid"
        anna.refresh_from_db()
        assert anna.login == OLD

    def test_a_password_change_invalidates_the_link(self, as_anna, anna):
        ask_change(as_anna, NEW)
        link = link_in(emails(CHANGE_TEMPLATE).get())
        anna.set_password(PASSWORD + "-nova")
        anna.save()
        _, done = open_and_confirm(link)
        assert done.context["state"] == "invalid"

    def test_address_taken_between_request_and_confirmation(self, as_anna, anna):
        """Abans de canviar-lo es torna a comprovar que l'adreça no és de cap altre compte."""
        ask_change(as_anna, NEW)
        link = link_in(emails(CHANGE_TEMPLATE).get())
        make_account(NEW, first="Avançada")
        page, done = open_and_confirm(link)
        assert done.context["state"] == "invalid"
        anna.refresh_from_db()
        assert anna.login == OLD
        assert not emails(NOTICE_TEMPLATE).exists()

    def test_tokens_of_other_purposes_do_not_work(self, anna):
        for purpose in (tokens.VERIFY_EMAIL, tokens.RESET_PASSWORD):
            client = Client()
            client.get(
                reverse("accounts:change_email_link", args=[tokens.make_token(anna, purpose)])
            )
            assert client.post(reverse(CONFIRM)).context["state"] == "invalid"
        anna.refresh_from_db()
        assert anna.login == OLD

    def test_confirmation_page_works_with_csrf_checks(self, as_anna, anna):
        """Regressió de la T-M01-05: la pàgina neta no envia «no-referrer», que faria que el
        navegador enviés «Origin: null» i el CSRF rebutgés el POST."""
        ask_change(as_anna, NEW)
        client = Client(enforce_csrf_checks=True)
        first = client.get(path_of(link_in(emails(CHANGE_TEMPLATE).get())))
        assert first["Referrer-Policy"] == "no-referrer"
        page = client.get(reverse(CONFIRM))
        assert page["Referrer-Policy"] == "same-origin"
        done = client.post(
            reverse(CONFIRM),
            {"csrfmiddlewaretoken": str(page.context["csrf_token"])},
            HTTP_ORIGIN="http://testserver",
        )
        assert done.context["state"] == "done"

    def test_invalid_address_shows_the_form_error(self, as_anna, anna):
        response = ask_change(as_anna, "no-es-cap-correu")
        assert response.status_code == 200
        assert response.context["email_form"].errors
        assert not EmailLinkRequest.objects.exists()

    def test_needs_a_personal_session(self, client, anna):
        response = client.post(reverse(CHANGE), {"new_email": NEW})
        assert response.status_code == 302
        assert response["Location"].startswith(reverse("accounts:login"))
        assert not OutgoingEmail.objects.exists()

    def test_other_sessions_stay_open(self, as_anna, anna, login_as):
        """Supòsit (no decidit): confirmar el correu nou no tanca la sessió oberta del compte."""
        ask_change(as_anna, NEW)
        open_and_confirm(link_in(emails(CHANGE_TEMPLATE).get()))
        assert as_anna.get(reverse(PROFILE)).status_code == 200
