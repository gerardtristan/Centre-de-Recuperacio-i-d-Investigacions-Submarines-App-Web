"""Socis inventats per a la revisió conjunta (T-M01-27). Només els crida `seed_demo_data`, que es
nega fora de desenvolupament amb `DEBUG` i amb una base que no sigui buida.

Cada cas passa pels serveis del 01 (alta presencial, aprovació, quotes, carnets, sol·licituds i
llicències), de manera que el registre d'activitat queda com quedaria de debò. Les poques
dreceres, marcades «shortcut», són per a coses que encara no tenen servei. Dades inventades:
documents de passaport `PROVAS…` i `PROVAT…` (només admesos a l'alta presencial), correus
`@example.org`, telèfons `+34 600 000 …` i cap IBAN.
"""

import datetime
import hashlib
from dataclasses import dataclass

from django.utils import timezone

from apps.accounts import email_links, tokens
from apps.accounts.models import Account
from apps.core import audit, charges, imports
from apps.core.models import Charge, ImportBatch, Payment, Person
from apps.core.persons import create_or_get

from . import admissions, cards, fees, join, licences, member_requests, services
from .imports import cluber_sample
from .models import (
    LicenceRecord,
    Member,
    MemberRequest,
    MembershipNumberCounter,
    MembershipType,
    MemberStatusChange,
)

ORIGIN = "seed_demo_data"
PASSPORT = Person.DocumentType.PASSPORT
CLUBER_NUMBER_OFFSET = 1000  # els números del fitxer de Cluber no toquen cap soci creat aquí


@dataclass
class Case:
    label: str
    member: Member | None  # None: alta pendent
    person: Person
    login: str = ""  # compte personal, si en té


@dataclass
class Result:
    cases: list
    valid_token: str  # testimoni del carnet vàlid (ple dret pagat)
    revoked_token: str  # testimoni del carnet revocat (de baixa)


class _Builder:
    def __init__(self, *, secretary, treasurer, admin, password):
        self.secretary, self.treasurer, self.admin = secretary, treasurer, admin
        self.password = password
        self.system = audit.system(ORIGIN)
        self.today = timezone.localdate()
        self.full = MembershipType.objects.get(code="full")
        self.supporter = MembershipType.objects.get(code="supporter")
        self.n = 0

    def born(self, age, month=3, day=15) -> datetime.date:
        return datetime.date(self.today.year - age, month, day)

    def submit(self, first, last, email, birth, mtype, *, guardian=False, **accept):
        """Alta presencial (P2) feta per la secretaria; sense rebut."""
        self.n += 1
        data = {
            "first_name": first,
            "last_name": last,
            "id_document_type": PASSPORT,
            "id_document_number": f"PROVAS{self.n:02d}",
            "contact_email": email,
            "phone": f"+34 600 000 1{self.n:02d}" if email else "",
            "address": "",
            "birth_date": birth,
            "membership_type": mtype,
            **{f"accept_{kind}": True for kind, given in accept.items() if given},
        }
        if guardian:
            data.update(
                guardian_first_name="Tutora",
                guardian_last_name=last,
                guardian_id_document_type=PASSPORT,
                guardian_id_document_number=f"PROVAT{self.n:02d}",
                guardian_email=f"representant.{self.n:02d}@example.org",
                guardian_phone=f"+34 600 000 2{self.n:02d}",
                guardian_authorization=True,
            )
        return join.submit(
            data, channel=MemberRequest.Channel.IN_PERSON, by=self.secretary, send_receipt=False
        ).request

    def approve(self, join_request) -> Member:
        return admissions.approve_join(
            join_request,
            by=self.secretary,
            identity_checked=admissions.needs_identity_check(join_request),
            guardian_checked=admissions.needs_guardian_check(join_request),
        )

    def pay(self, fee) -> None:
        """Pagament confirmat pel proveïdor (mode de proves) i avís al 01."""
        charges.record_payment(
            fee.charge,
            method=Payment.Method.CARD,
            origin="provider",
            by=self.system,
            provider_status="prova",
            provider_reference=f"PROVA-{fee.charge.pk}",
        )
        services.on_fee_paid(fee.pk)

    def paid_member(self, first, last, email, mtype, **accept) -> Member:
        member = self.approve(self.submit(first, last, email, self.born(40), mtype, **accept))
        self.pay(member.fees.get())
        member.refresh_from_db()
        return member

    def personal(self, person) -> Account:
        """Compte personal actiu, confirmat amb l'enllaç de verificació del correu (RN-18)."""
        account = Account.objects.create_personal(person, person.contact_email, self.password)
        email_links.confirm_email(tokens.make_token(account, tokens.VERIFY_EMAIL))
        account.refresh_from_db()
        return account

    def imported(self, number, first, last, email) -> Member:
        """Soci de la importació de Cluber, amb els mateixos passos que `imports.final._write`
        (el lot confirmat, la persona, el soci actiu, l'historial i el comptador)."""
        batch = ImportBatch.objects.filter(
            kind=ImportBatch.Kind.CLUBER, status=ImportBatch.Status.CONFIRMED
        ).first() or imports.open_confirmed(
            ImportBatch.Kind.CLUBER,
            file_sha256=hashlib.sha256(ORIGIN.encode()).hexdigest(),
            by=self.admin,
            counts={"new_count": 2},
        )
        person, _created, _check = create_or_get(
            origin=Person.Origin.CLUBER_IMPORT,
            import_batch=batch,
            first_name=first,
            last_name=last,
            contact_email=email,
            birth_date=datetime.date(1975, 6, 1),
        )
        member = Member.objects.create(
            person=person,
            member_number=number,
            type=self.full,
            status=Member.Status.ACTIVE,
            joined_on=datetime.date(2010, 3, 15),
            cluber_id=f"cl-prova-{number}",
            cluber_renewed_on=self.today - datetime.timedelta(days=60),
            import_batch=batch,
        )
        MemberStatusChange.objects.create(
            member=member,
            to_status=Member.Status.ACTIVE,
            to_type=member.type,
            effective_on=member.joined_on,
            actor_account=self.admin,
            origin=MemberStatusChange.Origin.CLUBER_IMPORT,
        )
        counter = MembershipNumberCounter.objects.select_for_update().get(pk=1)
        counter.last_number = max(counter.last_number, number)
        counter.save(update_fields=["last_number"])
        cards.issue_card(member, by=self.system)
        return member

    def unknown_licence(self, member) -> LicenceRecord:
        # shortcut: la caducitat desconeguda només ve de Cluber i la importació de llicències no
        # té servei encara (RN-M01-50); es crea com a les proves.
        return LicenceRecord.objects.create(
            member=member,
            licence_type="Llicència federativa (prova, de Cluber)",
            issued_on=datetime.date(self.today.year, 1, 20),
            expires_on=None,
            source=LicenceRecord.Source.CLUBER,
        )

    def supplement_case(self, first, last, email) -> tuple[Member, Account, MemberRequest]:
        member = self.paid_member(first, last, email, self.supporter)
        account = self.personal(member.person)
        change = member_requests.request_type_change(member, by=account)
        member_requests.approve_type_change(change, by=self.secretary)
        change.refresh_from_db()
        return member, account, change


def instructor_member(*, secretary, treasurer, admin, password) -> Member:
    """Un soci actiu de ple dret, amb la quota pagada, per fer d'instructor de prova (T-M02-30;
    RN-M02-26). Qui crida ja és dins d'una transacció i ha creat els casos de `create`."""
    b = _Builder(secretary=secretary, treasurer=treasurer, admin=admin, password=password)
    b.n = 90  # documents de prova diferents dels de `create`
    return b.paid_member("Biel", "Sard Instructor", "instructor.soci@example.org", b.full)


def create(*, secretary, treasurer, admin, password, with_cluber_batch=True) -> Result:
    """Crea tots els casos. Qui crida ja és dins d'una transacció."""
    b = _Builder(secretary=secretary, treasurer=treasurer, admin=admin, password=password)
    staff = secretary  # àlies: evita un fals positiu de la regla generic-api-key de gitleaks
    today, cases = b.today, []

    def add(label, member, account=None, person=None):
        person = person or member.person
        cases.append(Case(label, member, person, account.login if account else ""))

    if with_cluber_batch:
        unknown = b.imported(501, "Núria", "Corball Cluber", "importada.desconeguda@example.org")
        b.unknown_licence(unknown)
        add("Importat de Cluber, llicència amb caducitat desconeguda", unknown)
        declared = b.imported(502, "Ferran", "Rap Cluber", "importat.declarada@example.org")
        account = b.personal(declared.person)
        licences.declare_expiry(
            b.unknown_licence(declared), by=account, expires_on=datetime.date(today.year, 12, 31)
        )
        add("Importat de Cluber, caducitat declarada pel soci", declared, account)

    member = b.paid_member(
        "Laia", "Mero Prova", "simpatitzant.pagat@example.org", b.supporter, newsletter=True
    )
    add("Simpatitzant pagat", member)

    member = b.paid_member(
        "Pau", "Llobarro Prova", "ple.dret.pagat@example.org", b.full, images=True
    )
    account = b.personal(member.person)
    licences.add_record(
        member,
        by=staff,
        licence_type="Llicència federativa (prova)",
        issued_on=datetime.date(today.year, 1, 15),
        expires_on=datetime.date(today.year, 12, 31),
    )
    valid_token = cards.replace_card(member, by=b.system, reason="Dada de prova: testimoni conegut")
    add("Ple dret pagat, llicència amb caducitat coneguda, carnet vàlid", member, account)

    exempt_request = b.submit(
        "Biel",
        "Sard Prova",
        "exempt.edat@example.org",
        datetime.date(today.year - 14, 1, 1),  # 14 anys tot l'any
        b.supporter,
        guardian=True,
        newsletter=True,
    )
    member = b.approve(exempt_request)
    # Compte propi des dels 14 anys (072, Q-012).
    add("Exempt per edat (14 anys, amb correu propi)", member, b.personal(member.person))

    young = b.submit(
        "Mia",
        "Donzella Prova",
        "",
        b.born(10),
        b.supporter,
        guardian=True,
        images=True,
    )
    add("Menor de 14 anys amb representant (correu i telèfon)", b.approve(young))

    teen = b.submit("Pol", "Pop Prova", "", b.born(16, 2, 2), b.supporter, guardian=True)
    member = b.approve(teen)
    b.pay(member.fees.get())
    member.refresh_from_db()
    add("Menor de 14 a 17 anys sense correu propi (pagat)", member)

    member = b.paid_member("Marta", "Rap Prova", "impagat@example.org", b.full)
    fee = member.fees.get()
    # shortcut: la devolució la notificarà la 05b; fins aleshores, la transició de la 00.
    charges._transition(fee.charge, Charge.Status.RETURNED, by=b.system, reason="Prova")
    services.on_fee_returned(fee.pk)
    services.mark_unpaid(
        member,
        by=treasurer,
        effective_on=today,
        reason="Quota retornada pel banc (dada de prova).",
    )
    add("Impagat (quota retornada)", member)

    member = b.paid_member("Clara", "Dorada Prova", "canvi.pendent@example.org", b.supporter)
    account = b.personal(member.person)
    member_requests.request_type_change(member, by=account)
    add("Canvi a ple dret pendent", member, account)

    member, account, _change = b.supplement_case(
        "Oriol", "Serrà Prova", "suplement.pendent@example.org"
    )
    add("Canvi aprovat, suplement pendent", member, account)

    member, account, change = b.supplement_case(
        "Jordi", "Corball Prova", "suplement.vencut@example.org"
    )
    # shortcut: el suplement venç 7 dies després de l'aprovació (RN-M01-76); per veure'l vençut
    # avui, el venciment s'avança tres dies després d'aprovar-lo.
    supplement = change.supplement_fee
    supplement.due_on = today - datetime.timedelta(days=3)
    supplement.save(update_fields=["due_on"])
    add("Canvi aprovat, suplement vençut", member, account)

    member = b.paid_member("Arnau", "Sard Prova", "baixa.pendent@example.org", b.full)
    account = b.personal(member.person)
    member_requests.request_leave(member, by=account, reason="Canvi de ciutat (dada de prova).")
    add("Baixa pendent", member, account)

    member = b.paid_member("Anna", "Pop Prova", "baixa.programada@example.org", b.full)
    leave = member_requests.request_leave(
        member, by=staff, reason="Decisió de la junta (dada de prova)."
    )
    member_requests.approve_leave(leave, by=staff, effective_on=today + datetime.timedelta(days=30))
    add("Baixa programada d'aquí a 30 dies", member)

    member = b.paid_member("Joan", "Dorada Baixa", "de.baixa@example.org", b.full)
    revoked_token = cards.replace_card(
        member, by=b.system, reason="Dada de prova: testimoni conegut"
    )
    fees.issue_annual_fee(
        member,
        period=today.year + 1,
        due_on=datetime.date(today.year + 1, 1, 15),
        by=b.system,
    )
    leave = member_requests.request_leave(
        member, by=staff, reason="Ho demana per escrit (dada de prova)."
    )
    # Avui: estat «baixa», carnet revocat i la quota de l'any vinent anul·lada (RN-M01-20).
    member_requests.approve_leave(leave, by=staff, effective_on=today)
    member.refresh_from_db()
    add("De baixa (carnet revocat, quota de l'any vinent anul·lada)", member)

    adult = b.submit("Ona", "Llobarro Pendent", "alta.adult@example.org", b.born(30), b.full)
    add("Alta pendent (adult)", None, person=adult.person)
    minor = b.submit(
        "Èric", "Mero Pendent", "", b.born(12), b.supporter, guardian=True, newsletter=True
    )
    add("Alta pendent (menor de 14 anys)", None, person=minor.person)

    return Result(cases, valid_token, revoked_token)


def cluber_file() -> bytes:
    """Exportació de Cluber inventada (la mostra de les proves) sense cap IBAN i amb números que
    no coincideixen amb cap soci creat aquí."""
    rows = cluber_sample.sample_records()
    for row in rows:
        row["IBAN"] = ""
        row["Nº Soci"] = str(CLUBER_NUMBER_OFFSET + int(row["Nº Soci"]))
    return cluber_sample.to_file(rows)
