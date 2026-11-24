"""RGPD del 07 (T-M07-15; CA-M07-21, M07-12). Només dades inventades."""

import pytest

from apps.core import privacy
from apps.core.models import AuditEntry, LegalText, Person, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.website import contact, newsletter
from apps.website.models import ContactMessage, ContactReason, NewsletterSubscription

pytestmark = pytest.mark.django_db
S = NewsletterSubscription.Status


@pytest.fixture
def texts():
    return {
        kind: LegalText.objects.create(kind=kind, version=1, content=f"Text inventat {kind}")
        for kind in ("privacy", "newsletter")
    }


def _message(email, texts, **fields):
    return ContactMessage.objects.create(
        reason=ContactReason.objects.get(name="Quotes"), name="Mar Inventada", email=email,
        body="El meu telèfon és el 600 000 000", privacy_text=texts["privacy"], **fields,
    )  # fmt: skip


@pytest.fixture
def mar(texts, personal_account):
    """Una persona amb el correu de contacte i un compte personal amb un altre correu."""
    person = personal_account.person
    person.contact_email = "Mar.Inventada@example.org"
    person.save()
    _message("mar.inventada@EXAMPLE.org", texts)
    _message("anna@example.org", texts, status="answered", answer="Resposta inventada")
    newsletter.subscribe("mar.inventada@example.org", legal_text=texts["newsletter"])
    other = _message("una.altra@example.org", texts)
    newsletter.subscribe("una.altra@example.org", legal_text=texts["newsletter"])
    return person, other


def test_ca_m07_21_the_export_has_the_messages_and_the_subscriptions(mar):
    person, _ = mar
    data = privacy.export_person(person)["web"]
    assert sorted(m["correu"] for m in data["missatges_de_contacte"]) == [
        "anna@example.org",
        "mar.inventada@EXAMPLE.org",
    ]
    assert data["missatges_de_contacte"][0]["missatge"] == "El meu telèfon és el 600 000 000"
    assert [(s["correu"], s["versio_del_text"]) for s in data["butlleti"]] == [
        ("mar.inventada@example.org", 1)
    ]


def test_the_summary_says_what_will_happen_without_personal_data(mar):
    lines = privacy._MODULES["web"].describe(mar[0])
    assert lines == [
        "Té 2 missatges de contacte: se n'esborraran el nom, el correu i el text.",
        "Està subscrita al butlletí: es donarà de baixa.",
    ]


def test_ca_m07_21_the_erasure_removes_the_name_the_email_and_the_text(mar, make_admin):  # noqa: F811
    person, other = mar
    secretary = make_admin(Role.Code.SECRETARY)
    closed = ContactMessage.objects.get(email="anna@example.org")
    ContactMessage.objects.filter(pk=closed.pk).update(status="new", answer="")
    contact.close(closed, actor=secretary, reason="Ho ha demanat la Mar per telèfon")

    person = privacy.anonymise_person(person, by=make_admin(Role.Code.ADMINISTRATOR))

    ref = person.anonymous_ref
    for message in ContactMessage.objects.exclude(pk=other.pk):
        assert (message.name, message.body, message.answer) == (ref, "", "")
        assert message.email.startswith(ref.lower()) and message.status == "closed"
        assert message.finished_at and message.closed_reason == "Esborrat RGPD de la persona."
    entry = AuditEntry.objects.get(action=contact.ACTION_CLOSED)
    assert entry.reason == ref
    subscription = NewsletterSubscription.objects.exclude(email="una.altra@example.org").get()
    assert subscription.status == S.UNSUBSCRIBED and "mar" not in subscription.email
    assert list(subscription.events.values_list("kind", flat=True)) == [
        "requested",
        "unsubscribed",
    ]
    # Les dades d'una altra persona no es toquen.
    other.refresh_from_db()
    assert (other.name, other.email) == ("Mar Inventada", "una.altra@example.org")
    assert NewsletterSubscription.objects.filter(email="una.altra@example.org", status=S.PENDING)


def test_m07_12_an_unsubscription_keeps_only_the_trace(texts):
    sub, _ = newsletter.subscribe("baixa@example.org", legal_text=texts["newsletter"])
    newsletter.unsubscribe(sub.token)
    sub.refresh_from_db()
    assert sub.email == f"baixa-{sub.pk}@anonimitzat.invalid"
    assert (sub.status, sub.legal_text, bool(sub.unsubscribed_at)) == (
        S.UNSUBSCRIBED,
        texts["newsletter"],
        True,
    )


def test_the_erasure_works_without_any_account(texts, make_admin):  # noqa: F811
    person = Person.objects.create(
        first_name="Pere", contact_email="pere.inventat@example.org", origin="in_person"
    )
    _message("pere.inventat@example.org", texts)
    privacy.anonymise_person(person, by=make_admin(Role.Code.ADMINISTRATOR))
    assert not ContactMessage.objects.filter(email="pere.inventat@example.org").exists()


def test_p624_an_address_shared_with_another_person_is_neither_exported_nor_erased(
    texts,
    make_admin,  # noqa: F811
):
    """Revisió de la #587: un correu de contacte de família (dues persones actives)."""
    first = Person.objects.create(
        first_name="Pare", contact_email="familia@example.org", origin="in_person"
    )
    Person.objects.create(
        first_name="Filla", contact_email="Familia@example.org", origin="in_person"
    )
    shared = _message("familia@example.org", texts)
    newsletter.subscribe("familia@example.org", legal_text=texts["newsletter"])

    data = privacy.export_person(first)["web"]
    assert data == {"missatges_de_contacte": [], "butlleti": []}
    assert privacy._MODULES["web"].describe(first) == [
        "1 missatge de contacte i 1 subscripció al butlletí són d'una adreça que també té una "
        "altra persona: no es tocaran; cal revisar-los a mà."
    ]
    privacy.anonymise_person(first, by=make_admin(Role.Code.ADMINISTRATOR))
    shared.refresh_from_db()
    assert (shared.name, shared.email, shared.status) == (
        "Mar Inventada",
        "familia@example.org",
        "new",
    )
    assert NewsletterSubscription.objects.get().status == S.PENDING


def test_p624_a_role_mailbox_of_an_administrator_is_not_theirs(texts, make_admin):  # noqa: F811
    """Revisió de la #587: el correu de notificació d'un compte d'administrador no és únic."""
    from apps.accounts.models import Account
    from conftest import PASSWORD

    person = Person.objects.create(first_name="Joan", origin="in_person")
    Account.objects.create_admin(
        person, "joan.prova", PASSWORD, notification_email="secretaria@example.org"
    )
    mailbox = _message("secretaria@example.org", texts)
    assert privacy.export_person(person)["web"]["missatges_de_contacte"] == []
    privacy.anonymise_person(person, by=make_admin(Role.Code.ADMINISTRATOR))
    mailbox.refresh_from_db()
    assert mailbox.email == "secretaria@example.org" and mailbox.status == "new"


def test_a_contact_email_equal_to_the_admin_notification_email_is_still_theirs(
    texts,
    make_admin,  # noqa: F811
):
    """Revisió de la PR 1: el correu de contacte és de la persona encara que el compte
    d'administrador el faci servir per a les notificacions."""
    from apps.accounts.models import Account
    from conftest import PASSWORD

    person = Person.objects.create(
        first_name="Laia", contact_email="Laia.Inventada@example.org", origin="in_person"
    )
    Account.objects.create_admin(
        person, "laia.prova", PASSWORD, notification_email="laia.inventada@example.org"
    )
    own = _message("laia.inventada@example.org", texts)
    newsletter.subscribe("laia.inventada@example.org", legal_text=texts["newsletter"])
    data = privacy.export_person(person)["web"]
    assert len(data["missatges_de_contacte"]) == 1 and len(data["butlleti"]) == 1
    privacy.anonymise_person(person, by=make_admin(Role.Code.ADMINISTRATOR))
    own.refresh_from_db()
    assert own.email != "laia.inventada@example.org" and own.status == "closed"
    assert not NewsletterSubscription.objects.filter(email="laia.inventada@example.org").exists()
