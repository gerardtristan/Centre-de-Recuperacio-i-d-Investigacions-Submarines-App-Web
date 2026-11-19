"""Dades inventades i reproduïbles per a captures, demostracions i la revisió conjunta. Mai en
producció.

Crea persones fictícies, textos legals de prova (inclosos els provisionals del butlletí i de les
imatges, [A validar]), consentiments, un departament i càrrecs en diversos estats, i els socis de
la revisió (T-M01-27, `apps/members/demo_data.py`): quotes, carnets, sol·licituds, llicències i
un fitxer de Cluber inventat. També la tresoreria (T-M04-18, `apps/treasury/demo_data.py`):
moviments, liquidacions, extractes en CSV i Norma 43, conciliació i remeses. I els pagaments
(T-M05b-17, `apps/payments/demo_data.py`): intents en cada estat, notificacions, una remesa
liquidada, retornats, una devolució, convidats i mandats. Tot passa pels serveis, perquè el
registre d'activitat quedi com quedaria de debò.

Comptes de prova (074, punt 21): un d'administració per a cada rol de la revisió, amb la
contrasenya de proves i el mateix secret TOTP públic de prova, i comptes personals per a alguns
socis. Només es creen quan l'ordre pot córrer (`check_can_run`): fora de desenvolupament amb
`DEBUG`, o amb una base que no sigui local i buida, es nega i no crea res.

Entorn de proves (decisió 090; `config/settings/staging.py`): hi corre sense `DEBUG`, contra la
base del servidor («db»), i els comptes d'administració fan servir el secret TOTP del servidor
(`STAGING_TOTP_SECRET`), mai el de prova, que continua refusat sense `DEBUG` (RN-M01-84).
"""

import base64
import binascii
import random
import tempfile
import unicodedata
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account, TotpDevice
from apps.accounts.totp import DEMO_TOTP_SECRET
from apps.core import audit, charges, consents
from apps.core.crypto import encrypt
from apps.core.models import Charge, Consent, LegalText, Payment, Person, Role
from apps.core.roles import assign_role, grant_initial_administrator
from apps.members import demo_data
from apps.members.join import OPTIONAL_TEXT_CONTENT
from apps.payments import demo_data as payments_demo
from apps.treasury import demo_data as treasury_demo

ORIGIN = "seed_demo_data"
ADMIN_LOGIN = "admin-demo"
# L'única contrasenya de proves permesa (CLAUDE.md, `.gitleaks.toml`).
PASSWORD = "contrasenya-de-proves-1954"  # noqa: S105 (dada inventada de proves)
# Comptes d'administració de prova: identificador, nom i rol de la configuració inicial (059).
ROLE_ACCOUNTS = [
    (ADMIN_LOGIN, "Administració", Role.Code.ADMINISTRATOR),
    ("secretaria-demo", "Secretaria", Role.Code.SECRETARY),
    ("tresorer-demo", "Tresorer", Role.Code.TREASURER),
    ("president-demo", "President", Role.Code.PRESIDENT),
    ("instructor-demo", "Instructor", Role.Code.INSTRUCTOR),
]
CLUBER_FILE = Path(tempfile.gettempdir()) / "cris-cluber-inventat.csv"
ALLOWED_SETTINGS = {"config.settings.dev", "config.settings.test"}
STAGING_SETTINGS = "config.settings.staging"
LOCAL_HOSTS = {"", "localhost", "127.0.0.1", "::1"}  # "" és el sòcol local de PostgreSQL
DEFAULT_SEED = 1954
PEOPLE = 12

# Cognoms de fauna marina: no es poden confondre amb dades reals.
FIRST_NAMES = ["Anna", "Pau", "Laia", "Jordi", "Marta", "Oriol", "Núria", "Arnau", "Clara", "Biel"]
LAST_NAMES = ["Mero", "Llobarro", "Dorada", "Sard", "Pop", "Rap", "Corball", "Serrà", "Donzella"]


def demo_people(seed: int) -> list[dict]:
    """Les persones que crea l'ordre: sempre les mateixes per a la mateixa llavor."""
    rng = random.Random(seed)  # noqa: S311 (reproduïble a propòsit; no protegeix res)
    names = rng.sample([(f, la) for f in FIRST_NAMES for la in LAST_NAMES], PEOPLE)
    people = []
    for i, (first, last) in enumerate(names, start=1):
        ascii_name = unicodedata.normalize("NFKD", f"{first}.{last}").encode("ascii", "ignore")
        people.append(
            {
                "first_name": first,
                "last_name": last,
                # example.org és un domini reservat (RFC 2606): cap correu arriba a ningú.
                "contact_email": f"{ascii_name.decode().lower()}@example.org",
                "id_document_type": Person.DocumentType.PASSPORT,
                "id_document_number": f"PROVA{i:04d}",
                "origin": rng.choice([Person.Origin.WEB, Person.Origin.IN_PERSON]),
            }
        )
    return people


def is_staging() -> bool:
    """L'entorn de proves (090): la seva configuració i l'interruptor que només ella encén."""
    return settings.SETTINGS_MODULE == STAGING_SETTINGS and settings.DEMO_DATA_ALLOWED


def _valid_staging_secret(secret: str) -> bool:
    """Base32 d'almenys 160 bits (RFC 4226) i diferent del secret de prova, que és públic."""
    if not secret or secret == DEMO_TOTP_SECRET or len(secret) < 32:
        return False
    try:
        base64.b32decode(secret, casefold=True)
    except (binascii.Error, ValueError):
        return False
    return True


def totp_secret() -> str:
    """El secret dels comptes de prova: el del servidor a l'entorn de proves; si no, el de prova."""
    return settings.STAGING_TOTP_SECRET if is_staging() else DEMO_TOTP_SECRET


def check_can_run() -> None:
    staging = is_staging()
    if not staging and (settings.SETTINGS_MODULE not in ALLOWED_SETTINGS or not settings.DEBUG):
        raise CommandError(
            "Només s'executa en desenvolupament o proves, amb DEBUG actiu. Mai en producció."
        )
    if staging and not _valid_staging_secret(settings.STAGING_TOTP_SECRET):
        raise CommandError(
            "A l'entorn de proves cal STAGING_TOTP_SECRET: base32 propi del servidor, de 32 "
            "caràcters o més, mai el secret de prova."
        )
    hosts = LOCAL_HOSTS | set(settings.DEMO_DATA_DB_HOSTS) if staging else LOCAL_HOSTS
    if connection.settings_dict["HOST"] not in hosts:
        raise CommandError("Només s'executa amb una base de dades local.")
    if Person.objects.exists() or Account.objects.exists() or LegalText.objects.exists():
        raise CommandError(
            "La base de dades no és buida. Fes servir una base de dades nova i migrada."
        )


def _admin_account(login: str, first_name: str) -> Account:
    """Compte d'administració de prova, operatiu: contrasenya de proves i TOTP de prova."""
    person = Person.objects.create(
        first_name=first_name, last_name="Demo", origin=Person.Origin.IN_PERSON
    )
    account = Account.objects.create_admin(person, login, password=PASSWORD)
    TotpDevice.objects.create(
        account=account, secret_encrypted=encrypt(totp_secret()), confirmed_at=timezone.now()
    )
    return account


class Command(BaseCommand):
    help = "Crea dades inventades (persones, socis i comptes de prova) per a captures i revisió."

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="llavor fixa")
        parser.add_argument(
            "--cluber-file", type=Path, default=CLUBER_FILE, help="on es desa el fitxer de Cluber"
        )
        parser.add_argument(
            "--without-cluber-batch",
            action="store_true",
            help="sense els socis importats ni el lot confirmat, per provar la previsualització",
        )

    def handle(self, *args, seed, cluber_file, without_cluber_batch, **options):
        check_can_run()
        with transaction.atomic():
            counts, review = self._create(seed, with_cluber_batch=not without_cluber_batch)
        cluber_file.write_bytes(demo_data.cluber_file())
        out = self.stdout.write
        out(
            f"Llavor {seed}: {counts['people']} persones, {counts['charges']} càrrecs, "
            f"{counts['consents']} consentiments."
        )
        treasury = counts["treasury"]
        out(
            f"Tresoreria: {treasury['movements']} moviments, {treasury['settlements']} "
            f"liquidacions, {treasury['statements']} extractes (CSV i Norma 43) i remeses "
            f"«{treasury['remittances'][0]}» i «{treasury['remittances'][1]}»."
        )
        payments = counts["payments"]
        out(
            f"Pagaments: {payments['attempts']} intents, {payments['notifications']} "
            "notificacions, una remesa liquidada amb dos rebuts retornats, una devolució, "
            "pagaments de convidats i mandats actius, revocat, caducat i bloquejat."
        )
        out("")
        out(f"Administració: {reverse('administration:login')}  (contrasenya: {PASSWORD})")
        for login, _name, role in ROLE_ACCOUNTS:
            out(f"  {login:<16} {Role.Code(role).label}")
        if is_staging():
            # El secret del servidor no surt als registres: el rep la bústia de proves.
            out("Codi TOTP: el secret STAGING_TOTP_SECRET del servidor (el mateix per a tots).")
        else:
            out(f"Codi TOTP de prova: secret {DEMO_TOTP_SECRET} (el mateix per a tots).")
            out("  Afegeix-lo a una app d'autenticació o calcula el codi amb:")
            out(f"  python -c \"import pyotp; print(pyotp.TOTP('{DEMO_TOTP_SECRET}').now())\"")
        out("")
        out(f"Àrea personal: {reverse('accounts:login')}  (contrasenya: {PASSWORD})")
        for case in review.cases:
            number = f"núm. {case.member.member_number}" if case.member else "sense número"
            login = f" · entra amb {case.login}" if case.login else ""
            name = f"{case.person.first_name} {case.person.last_name}"
            out(f"  {case.label}: {name}, {number}{login}")
        out("")
        out(f"Carnet vàlid: {reverse('members:card_verify', args=[review.valid_token])}")
        out(f"Carnet revocat: {reverse('members:card_verify', args=[review.revoked_token])}")
        out(f"Fitxer de Cluber inventat: {cluber_file}")
        if not without_cluber_batch:
            out(
                "  Aquesta base ja té una importació de Cluber confirmada: la previsualització "
                "el rebutjarà. Per provar-la, carrega una base nova amb --without-cluber-batch."
            )

    def _create(self, seed: int, *, with_cluber_batch: bool):
        rng = random.Random(seed)  # noqa: S311 (reproduïble a propòsit; no protegeix res)
        system = audit.system(ORIGIN)

        accounts = {role: _admin_account(login, name) for login, name, role in ROLE_ACCOUNTS}
        admin = accounts[Role.Code.ADMINISTRATOR]
        grant_initial_administrator(admin, origin=ORIGIN)
        for role, account in accounts.items():
            if role != Role.Code.ADMINISTRATOR:
                assign_role(account, role, by=admin)

        for kind, content in [
            ("privacy", "Text de prova de la política de privacitat, versió 1."),
            ("privacy", "Text de prova de la política de privacitat, versió 2."),
            # Butlletí i imatges: textos PROVISIONALS [A validar: Q-16 i Q-028] (074, punt 16).
            *OPTIONAL_TEXT_CONTENT.items(),
            # Formulari d'alta (T-M01-13). Textos de prova: no serveixen per a producció (H1).
            ("membership_terms", "Text de prova de les condicions de soci, versió 1."),
            ("adult_declaration", "Text de prova: declaro que soc major d'edat."),
            # Alta d'un menor (068): l'autorització del pare, la mare o el tutor legal.
            (
                "guardian_authorization",
                "Text de prova: com a pare, mare o tutor legal, autoritzo l'alta del menor.",
            ),
        ]:
            consents.publish_text(kind, content, by=admin)

        activities = charges.create_department("Activitats (prova)", by=admin)

        people = [Person.objects.create(**fields) for fields in demo_people(seed)]
        n_consents = n_charges = 0
        for person in people:
            in_person = person.origin == Person.Origin.IN_PERSON
            channel = Consent.Channel.IN_PERSON if in_person else Consent.Channel.WEB
            by = admin if in_person else None
            consents.grant(person, "privacy", channel=channel, by=by)
            n_consents += 1
            if rng.random() < 0.5:
                consents.grant(person, "newsletter", channel=channel, by=by)
                n_consents += 1
                if rng.random() < 0.3:
                    consents.withdraw(person, "newsletter", channel=channel, by=by)
                    n_consents += 1

            fee = charges.create_charge(
                person,
                kind=Charge.Kind.FEE,
                amount_cents=5000,
                concept="Quota de prova",
                origin=ORIGIN,
                by=system,
            )
            n_charges += 1
            outcome = rng.choice(["pending", "paid", "paid", "cancelled"])
            if outcome == "paid":
                charges.record_payment(
                    fee,
                    method=Payment.Method.CARD,
                    origin="provider",
                    by=system,
                    provider_status="prova",
                    provider_reference=f"PROVA-{fee.pk}",
                )
            elif outcome == "cancelled":
                charges.cancel(fee, "Dada de prova: anul·lat per mostrar l'estat.", by=admin)

            if rng.random() < 0.4:
                charges.create_charge(
                    person,
                    kind=Charge.Kind.ENROLMENT,
                    amount_cents=rng.choice([2500, 4000, 12000]),
                    concept="Inscripció de prova",
                    origin=ORIGIN,
                    department=activities,
                    by=system,
                )
                n_charges += 1

        review = demo_data.create(
            secretary=accounts[Role.Code.SECRETARY],
            treasurer=accounts[Role.Code.TREASURER],
            admin=admin,
            password=PASSWORD,
            with_cluber_batch=with_cluber_batch,
        )
        # Pagaments (T-M05b-17): el mandat caducat va abans de cap altre mandat (vegeu el mòdul).
        payments_demo.expired_mandate(admin=admin, review=review)
        # Tresoreria (T-M04-18): moviments, liquidacions, extractes, conciliació i remeses.
        treasury = treasury_demo.create(
            treasurer=accounts[Role.Code.TREASURER],
            secretary=accounts[Role.Code.SECRETARY],
            admin=admin,
            review=review,
            password=PASSWORD,
        )
        # Pagaments (T-M05b-17): intents, notificacions, remesa liquidada, retornats, devolució,
        # convidats i mandats.
        payments = payments_demo.create(
            treasurer=accounts[Role.Code.TREASURER], admin=admin, review=review
        )
        counts = {"people": len(people), "charges": n_charges, "consents": n_consents}
        return {**counts, "treasury": treasury, "payments": payments}, review
