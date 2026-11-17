"""Dades inventades dels pagaments (T-M05b-17): perquè una base local nova ensenyi el llistat de
pagaments i «a revisar», les notificacions, una remesa liquidada, els retornats, una devolució, un
pagament de convidat i els mandats en cada estat.

Ho crida `seed_demo_data`, que ja comprova que només corre en local i amb una base buida. Tot passa
pels serveis (pagament, notificacions per l'endpoint i la cua, remeses, retornats, devolucions,
enllaços de convidat i mandats), perquè les regles i el registre d'activitat quedin com quedarien
de debò. Cap dada real: imports, conceptes i IBAN inventats, i l'identificador de creditor de prova.

Dues crides: `expired_mandate` abans de la tresoreria (és l'únic mandat actiu en aquell moment, i
la caducitat es calcula per a tots alhora) i `create` després, que fa servir la remesa avisada de
la tresoreria. Les ordres del proveïdor fals viuen a la memòria del procés: quan l'ordre acaba,
el Bizum que queda en curs ja no el troba, i la xarxa de seguretat el deixarà «a revisar».

Cap intent queda «creat»: és un estat de pas dins de `start_payment`.
"""

import json
from contextlib import contextmanager
from uuid import uuid4

from django.test import RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.core import audit, charges, consents, guest_links
from apps.core.models import Charge, Department, LegalText, Person
from apps.treasury import demo_data as treasury_demo

from . import (
    checkout,
    expiry,
    mandates,
    processing,
    refunds,
    remittances,
    returns,
    sepa_xml,
    webhooks,
)
from .models import DirectDebitRemittance, PaymentAttempt, ProviderEvent
from .providers import base, fake, get_provider

ORIGIN = "seed_demo_data"
CLUB_IBAN = treasury_demo.iban(999)  # compte del club inventat, només per generar el fitxer


@contextmanager
def _club():
    """El fitxer pain.008 i la transferència demanen l'identificador de creditor i l'IBAN del
    club (VC-09), que en local solen ser buits: aquí, valors de prova només durant la crida."""
    with override_settings(
        SEPA_CREDITOR_IDENTIFIER=treasury_demo.CREDITOR, CLUB_IBAN_TRANSFERENCIES=CLUB_IBAN
    ):
        yield


def _notify(order_id: str, status: str, *, event_id=None, amount_cents=None, signed=True):
    """La notificació del proveïdor fals, rebuda per l'endpoint (firma, desar, cua) i processada
    com ho faria la cua. Torna el resultat."""
    provider = get_provider()
    body, headers = fake.FakeProvider().notification(order_id, status, event_id=event_id)
    if amount_cents is not None:
        body = json.dumps({**json.loads(body), "amount_cents": amount_cents}, sort_keys=True)
        body = body.encode()
        headers = {fake.SIGNATURE_HEADER: fake.sign(body)}
    if not signed:
        headers = {fake.SIGNATURE_HEADER: "0" * 64}
    path = reverse("payments:provider_notification", args=[provider.code])
    request = RequestFactory().post(path, body, content_type="application/json", headers=headers)
    received = webhooks.receive(provider, request)
    if received.event is None or received.event.result != ProviderEvent.Result.RECEIVED:
        return received
    processing.process_notification(received.event.pk)
    return received


def _charge(person, concept, cents, department):
    return charges.create_charge(
        person,
        kind=Charge.Kind.ENROLMENT,
        amount_cents=cents,
        concept=concept,
        origin=ORIGIN,
        department=department,
        by=audit.system(ORIGIN),
    )


def _start(charge, method, payer):
    start = checkout.start_payment(charge, method, payer)
    return PaymentAttempt.objects.get(pk=start.attempt_id)


def _sign(member, account, n, text):
    return mandates.create_mandate(
        member,
        iban=treasury_demo.iban(n),
        holder_name=f"{member.person.first_name} {member.person.last_name}",
        holder_is_member=True,
        legal_text=text,
        account=account,
        creditor_identifier=treasury_demo.CREDITOR,
        evidence={"channel": "web", "origin": ORIGIN},
    )


def _case(review, label):
    case = next(case for case in review.cases if case.label == label)
    return case, case.person.accounts.get(login=case.login)


def expired_mandate(*, admin, review) -> None:
    """Un mandat caducat (RN-M05a-08): signat avui i, sense cap cobrament, caducat amb la tasca
    diària en la data dels 36 mesos. Abans de cap altre mandat: la tasca els mira tots."""
    text = consents.publish_text("sepa_mandate", treasury_demo.SEPA_TEXT, by=admin)
    case, account = _case(review, "Baixa pendent")
    mandate = _sign(case.member, account, 41, text)
    expiry.expire_mandates(expiry.expires_on(mandate))


def create(*, treasurer, admin, review) -> dict:
    """Crea les dades dels pagaments. Qui crida ja és dins d'una transacció. Torna un resum."""
    activities = Department.objects.get(name="Activitats (prova)")
    guests = list(
        Person.objects.filter(id_document_number__startswith="PROVA").order_by(
            "id_document_number"
        )[3:9]
    )

    def guest(index, concept, cents):
        charge = _charge(guests[index], concept, cents, activities)
        return charge, guest_links.create(charge.person, charge, by=audit.system(ORIGIN))

    # Un soci que paga amb targeta: pagat per la notificació, repetida una vegada (ignorada).
    case, account = _case(review, "Ple dret pagat, llicència amb caducitat coneguda, carnet vàlid")
    outing = _charge(case.person, "Sortida a les Medes (prova)", 4500, activities)
    paid = _start(outing, "card", account)
    _notify(paid.provider_order_id, base.PAID, event_id="demo-pagat")
    _notify(paid.provider_order_id, base.PAID, event_id="demo-pagat")
    # Devolució parcial pel proveïdor (B5): el càrrec continua pagat.
    refunds.refund(
        paid.charge.payments.get(),
        1500,
        reason="Sortida escurçada pel mal temps (dada de prova).",
        key=uuid4(),
        by=treasurer,
    )

    # Convidats amb l'enllaç de la 00 (decisió 021): pagat, denegat, caducat i «a revisar».
    charge, link = guest(0, "Curs Open Water (prova)", 12000)
    _notify(_start(charge, "card", link).provider_order_id, base.PAID)
    charge, link = guest(1, "Bateig de mar (prova)", 3000)
    _notify(_start(charge, "card", link).provider_order_id, base.DENIED)
    charge, link = guest(2, "Llicència d'un dia (prova)", 1500)
    _notify(_start(charge, "bizum", link).provider_order_id, base.EXPIRED)
    charge, link = guest(3, "Curs de nitrox (prova)", 9000)
    _notify(_start(charge, "card", link).provider_order_id, base.PAID, amount_cents=900)
    # Transferència començada i després targeta: la transferència queda abandonada (P-136) i la
    # targeta en curs. I un Bizum que espera la confirmació a l'app del banc.
    charge, link = guest(4, "Curs de rescat (prova)", 8000)
    with _club():
        _start(charge, "transfer", link)
    _start(charge, "card", link)
    charge, link = guest(5, "Immersió nocturna (prova)", 2500)
    _start(charge, "bizum", link)
    # Notificacions que no arriben a cap intent: una sense firma vàlida i una d'una ordre que la
    # plataforma no coneix (oberta directament al proveïdor fals, sense intent).
    _notify(paid.provider_order_id, base.PAID, signed=False)
    urls = base.OrderUrls("https://a.invalid", "https://b.invalid", "https://c.invalid")
    stray = get_provider().create_order(paid.charge, base.CARD, urls, uuid4())
    _notify(stray.external_id, base.PAID)

    # La remesa avisada de la tresoreria: fitxer, enviada, liquidada amb l'abonament del banc i,
    # després, dos rebuts retornats amb la proposta pendent del tresorer.
    remittance = DirectDebitRemittance.objects.get(status=DirectDebitRemittance.Status.NOTIFIED)
    with _club():
        sepa_xml.remittance_file(remittance, treasurer)
    remittances.mark_remittance_sent(remittance, file_deleted=True, by=treasurer)
    today = timezone.localdate()
    days_ahead = (remittance.collection_date - today).days
    text = f"ABONAMENT REMESA SEPA {remittance.period}"
    batch = treasury_demo._import(
        treasury_demo._csv(today, [(-days_ahead, text, remittance.total_cents)]), treasurer
    )
    remittances.settle_remittance(remittance, treasury_demo._line(batch, text), by=treasurer)
    first, second = remittance.items.order_by("pk")
    proposals = (
        returns.register_return(first, "AM04", fee_cents=300, by=treasurer),  # reintent
        returns.register_return(second, "MD01", by=treasurer),  # mandat bloquejat
    )

    # Un mandat revocat pel mateix soci (P-M05a-C).
    case, account = _case(review, "Canvi aprovat, suplement pendent")
    legal = LegalText.objects.filter(kind="sepa_mandate").latest("version")
    _sign(case.member, account, 42, legal)
    mandates.revoke_mandate(case.member, by=account)

    return {
        "attempts": PaymentAttempt.objects.count(),
        "notifications": ProviderEvent.objects.count(),
        "proposals": proposals,
    }
