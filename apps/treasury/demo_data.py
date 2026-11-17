"""Dades inventades de la tresoreria (T-M04-18): perquè una base local nova ensenyi les pantalles
de comptes i saldos, moviments, conciliació, «a revisar» i les remeses amb dades versemblants.

Ho crida `seed_demo_data`, que ja comprova que només corre en local i amb una base buida. Tot
passa pels serveis (ingressos, liquidacions, extractes, conciliació, traspàs, arqueig, mandats i
remeses), perquè les regles i el registre d'activitat quedin com quedarien de debò. Cap dada real:
els IBAN són de format vàlid amb un banc i un compte de zeros, els conceptes són inventats i
l'identificador de creditor és de prova.
"""

import datetime

from django.conf import settings
from django.utils import timezone

from apps.accounts import email_links, tokens
from apps.accounts.models import Account
from apps.core import audit, charges, consents, persons
from apps.core.imports import bank_statement, statement_lines
from apps.core.models import Charge, ImportBatch, Payment, Person
from apps.members import admissions, fees, join
from apps.members.models import MemberRequest, MembershipType
from apps.payments import mandates, preferences, remittances

from . import reconciliation, references, services, settlements
from .models import Movement, TreasuryAccount
from .settlements import SettlementData, SettlementLine

ORIGIN = "seed_demo_data"
CREDITOR = "ES00ZZZ00000000"  # identificador de creditor de prova (format SEPA, inventat)
SEPA_TEXT = "Text de prova del mandat SEPA. No serveix per a producció."
FEE_CENTS = 25  # comissió inventada del proveïdor per cobrament


def iban(n: int) -> str:
    """IBAN espanyol inventat amb els dígits de control correctes: banc 0000 i compte de zeros."""
    bban = f"{n:020d}"
    check = 98 - int(bban + "142800") % 97
    return f"ES{check:02d}{bban}"


def _euros(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    return f"{sign}{abs(cents) // 100},{abs(cents) % 100:02d}"


def _csv(today, rows) -> bytes:
    """Extracte en CSV amb el perfil del banc (`BANK_STATEMENT_CSV_PROFILE`): data, concepte,
    import i saldo, amb «;» i coma decimal."""
    lines, balance = ["Data;Concepte;Import;Saldo"], 250_000
    for days_ago, concept, cents in rows:
        balance += cents
        day = today - datetime.timedelta(days=days_ago)
        lines.append(f"{day:%d/%m/%Y};{concept};{_euros(cents)};{_euros(balance)}")
    return "\n".join(lines).encode()


def _norma43(today, rows) -> bytes:
    """Extracte en Norma 43 (quadern 43 de l'AEB), amb el compte de la capçalera de zeros."""
    opening, balance, debits, credits = 250_000, 250_000, [], []
    records = [f"11{'0' * 18}{today:%y%m%d}{today:%y%m%d}2{opening:014d}9783{'CRIS PROVES':<26}   "]
    for days_ago, concept, cents in rows:
        day = f"{today - datetime.timedelta(days=days_ago):%y%m%d}"
        sign = "2" if cents > 0 else "1"
        (credits if cents > 0 else debits).append(abs(cents))
        balance += cents
        records.append(
            f"22{'':4}0000{day}{day}02000{sign}{abs(cents):014d}{'0' * 10}{'':>12}{'':<16}"
        )
        records.append(f"2301{concept:<76}")
    records.append(
        f"33{'0' * 18}{len(debits):05d}{sum(debits):014d}{len(credits):05d}{sum(credits):014d}"
        f"2{balance:014d}978    "
    )
    records.append("88" + "9" * 18 + f"{len(records) + 1:06d}" + " " * 54)
    return "\r\n".join(records).encode("ascii")


def _import(data: bytes, by) -> ImportBatch:
    preview = bank_statement.preview(data, by=by)
    return bank_statement.confirm(preview["token"], by=by)


def _line(batch, text):
    return statement_lines(batch).get(concept__contains=text)


def _card_payment(charge, system):
    return charges.record_payment(
        charge,
        method=Payment.Method.CARD,
        origin="provider",
        by=system,
        provider_status="prova",
        provider_reference=f"PROVA-{charge.pk}",
    )


def _new_member(secretary):
    """Alta presencial aprovada (P2 i P3), amb la primera quota pendent i vençuda avui."""
    request = join.submit(
        {
            "first_name": "Quim",
            "last_name": "Rap Remesa",
            "id_document_type": Person.DocumentType.PASSPORT,
            "id_document_number": "PROVAR01",
            "contact_email": "remesa.sense.correu@example.org",
            "phone": "+34 600 000 199",  # inventat; sense correu, el telèfon és l'únic contacte
            "address": "",
            "birth_date": datetime.date(1980, 5, 20),
            "membership_type": MembershipType.objects.get(code="full"),
        },
        channel=MemberRequest.Channel.IN_PERSON,
        by=secretary,
        send_receipt=False,
    ).request
    return admissions.approve_join(
        request,
        by=secretary,
        identity_checked=admissions.needs_identity_check(request),
        guardian_checked=admissions.needs_guardian_check(request),
    )


def create(*, treasurer, secretary, admin, review, password) -> dict:
    """Crea les dades de la tresoreria. Qui crida ja és dins d'una transacció. Torna un resum."""
    system = audit.system(ORIGIN)
    today = timezone.localdate()
    bank = TreasuryAccount.objects.get(name="Banc principal")
    cash = TreasuryAccount.objects.get(name="Caixa")

    # Inscripcions pagades amb targeta: ingressos a «Activitats (prova)», no només a «General».
    for charge in Charge.objects.filter(
        kind=Charge.Kind.ENROLMENT, status=Charge.Status.PENDING
    ).order_by("pk")[:2]:
        _card_payment(charge, system)
    # Tots els cobraments amb targeta de les dades de prova, apuntats al trànsit del proveïdor.
    card = Payment.objects.filter(
        method=Payment.Method.CARD, charge__status=Charge.Status.PAID
    ).order_by("pk")
    for payment in card.exclude(movements__kind=Movement.Kind.INCOME):
        services.record_income(payment, origin="provider", by=system)

    # Liquidacions del proveïdor: una conciliada, una rebuda i una «a revisar».
    def settle(external_id, payments, extra=()):
        lines = tuple(SettlementLine(p.provider_reference, p.amount_cents) for p in payments)
        lines += tuple(extra)
        gross = sum(line.amount_cents for line in lines)
        fee = FEE_CENTS * len(lines)
        data = SettlementData(external_id, today, gross, fee, gross - fee, lines)
        return settlements.record_settlement(settings.PAYMENTS_PROVIDER, data, by=system)

    card = list(card)
    reconciled = settle("LIQ-PROVA-001", card[:3])
    settlements.confirm(reconciled, by=treasurer)
    settle("LIQ-PROVA-002", card[3:5])
    settle("LIQ-PROVA-003", card[5:6], [SettlementLine("PROVA-DESCONEGUDA", 4000)])

    # Extractes: un en CSV i un en Norma 43, amb transferències de quotes pendents.
    paid, proposed, n43_charge = (
        charges.create_charge(
            person,
            kind=Charge.Kind.FEE,
            amount_cents=5000,
            concept="Quota de prova (per transferència)",
            origin=ORIGIN,
            by=system,
        )
        for person in Person.objects.filter(id_document_number__startswith="PROVA").order_by(
            "id_document_number"
        )[:3]
    )
    csv_batch = _import(
        _csv(
            today,
            [
                (6, f"ABONAMENT LIQUIDACIO TPV {reconciled.external_id}", reconciled.net_cents),
                (5, f"TRANSF {references.transfer_reference(paid)} QUOTA", paid.amount_cents),
                (
                    4,
                    f"TRANSF {references.transfer_reference(proposed)} QUOTA",
                    proposed.amount_cents,
                ),
                (3, "TRANSF D'UNA ALTRA ENTITAT (PROVA)", 4500),
                (2, "COMISSIO MANTENIMENT COMPTE (PROVA)", -300),
            ],
        ),
        treasurer,
    )
    n43_text = f"TRANSF {references.transfer_reference(n43_charge)} QUOTA"
    _import(
        _norma43(today, [(1, n43_text, n43_charge.amount_cents), (1, "REBUT AIGUA LOCAL", -2150)]),
        treasurer,
    )
    reconciliation.refresh()
    reconciliation.confirm(_line(csv_batch, references.transfer_reference(paid)), by=treasurer)
    reason = "Transferència d'una altra entitat que no és nostra (dada de prova)."
    reconciliation.exclude(_line(csv_batch, "ALTRA ENTITAT"), reason=reason, by=treasurer)

    # Traspàs a la caixa, arqueig amb una diferència ajustada i un ajust anul·lat.
    services.record_transfer(
        bank,
        cash,
        10_000,
        value_date=today,
        concept="Retirada per a la caixa (prova)",
        by=treasurer,
    )
    services.record_cash_count(
        cash,
        9_650,
        counted_on=today,
        by=treasurer,
        adjustment_reason="Falten 3,50 € al recompte (dada de prova).",
    )
    count = services.record_cash_count(
        cash, 9_950, counted_on=today, by=treasurer, adjustment_reason="Recompte repetit (prova)."
    )
    services.reverse(
        count.adjustment,
        reason="El segon recompte estava mal fet (dada de prova).",
        by=treasurer,
    )

    # Remeses: una avisada i una en esborrany (un deutor sense adreça, P-232).
    text = consents.publish_text("sepa_mandate", SEPA_TEXT, by=admin)

    def direct_debit(member, account, n):
        mandates.create_mandate(
            member,
            iban=iban(n),
            holder_name=f"{member.person.first_name} {member.person.last_name}",
            holder_is_member=True,
            legal_text=text,
            account=account,
            creditor_identifier=CREDITOR,
            evidence={"channel": "web", "origin": ORIGIN},
        )
        preferences.set_preference(member, "direct_debit", by=account)

    by_label = {case.label: case for case in review.cases}
    for n, label in enumerate(
        [
            "Ple dret pagat, llicència amb caducitat coneguda, carnet vàlid",
            "Canvi a ple dret pendent",
        ],
        start=1,
    ):
        case = by_label[label]
        fees.issue_annual_fee(case.member, period=today.year + 1, due_on=today, by=system)
        direct_debit(case.member, case.person.accounts.get(login=case.login), n)
    collection = remittances.earliest_collection_date(today)
    notified = remittances.build_remittance(f"{today.year + 1}", collection, treasurer)

    # Un soci nou amb la primera quota per domiciliació, que després es queda sense adreça.
    member = _new_member(secretary)
    account = Account.objects.create_personal(member.person, member.person.contact_email, password)
    email_links.confirm_email(tokens.make_token(account, tokens.VERIFY_EMAIL))  # compte actiu
    direct_debit(member, account, 3)
    persons.update(member.person, by=secretary, contact_email="")
    draft = remittances.build_remittance(f"{today.year + 1}-b", collection, treasurer)

    return {
        "movements": Movement.objects.count(),
        "settlements": 3,
        "statements": 2,
        "remittances": (notified.get_status_display(), draft.get_status_display()),
    }
