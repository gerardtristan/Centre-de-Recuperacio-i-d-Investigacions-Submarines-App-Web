"""Dades inventades i reproduïbles per a captures i demostracions. Mai en producció.

Crea persones fictícies, textos legals de prova, consentiments, un departament i càrrecs en
diversos estats, a través dels serveis de la 00, perquè el registre d'activitat quedi com
quedaria de debò. Crea també el compte `admin-demo` amb el rol administrador, però sense
contrasenya ni TOTP: no és operatiu fins que algú li posa contrasenya (`changepassword`) i dona
d'alta el TOTP des del navegador. L'ordre no mostra cap contrasenya, secret ni QR.
"""

import random
import unicodedata

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

from apps.accounts.models import Account
from apps.core import audit, charges, consents
from apps.core.models import Charge, Consent, LegalText, Payment, Person
from apps.core.roles import grant_initial_administrator

ORIGIN = "seed_demo_data"
ADMIN_LOGIN = "admin-demo"
ALLOWED_SETTINGS = {"config.settings.dev", "config.settings.test"}
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


def check_can_run() -> None:
    if settings.SETTINGS_MODULE not in ALLOWED_SETTINGS or not settings.DEBUG:
        raise CommandError(
            "Només s'executa en desenvolupament o proves, amb DEBUG actiu. Mai en producció."
        )
    if connection.settings_dict["HOST"] not in LOCAL_HOSTS:
        raise CommandError("Només s'executa amb una base de dades local.")
    if Person.objects.exists() or Account.objects.exists() or LegalText.objects.exists():
        raise CommandError(
            "La base de dades no és buida. Fes servir una base de dades nova i migrada."
        )


class Command(BaseCommand):
    help = "Crea dades inventades i reproduïbles (persones fictícies) per a captures."

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="llavor fixa")

    def handle(self, *args, seed, **options):
        check_can_run()
        with transaction.atomic():
            counts = self._create(seed)
        self.stdout.write(
            f"Llavor {seed}: {counts['people']} persones, {counts['charges']} càrrecs, "
            f"{counts['consents']} consentiments."
        )
        self.stdout.write(
            f"El compte «{ADMIN_LOGIN}» té el rol administrador, però no és operatiu. "
            f"Posa-li contrasenya amb «python manage.py changepassword {ADMIN_LOGIN}» i dona "
            "d'alta el TOTP entrant per l'administració. No capturis aquelles dues pantalles."
        )

    def _create(self, seed: int) -> dict:
        rng = random.Random(seed)  # noqa: S311 (reproduïble a propòsit; no protegeix res)
        system = audit.system(ORIGIN)

        admin_person = Person.objects.create(
            first_name="Administració", last_name="Demo", origin=Person.Origin.IN_PERSON
        )
        # Sense contrasenya: el compte no es pot fer servir fins a `changepassword` i el TOTP.
        admin = Account.objects.create_admin(admin_person, ADMIN_LOGIN)
        grant_initial_administrator(admin, origin=ORIGIN)

        for kind, content in [
            ("privacy", "Text de prova de la política de privacitat, versió 1."),
            ("privacy", "Text de prova de la política de privacitat, versió 2."),
            ("newsletter", "Text de prova: vull rebre el butlletí."),
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
                payment = Payment.objects.create(
                    charge=fee,
                    method=Payment.Method.CARD,
                    amount_cents=fee.amount_cents,
                    provider_status="prova",
                    provider_reference=f"PROVA-{fee.pk}",
                    paid_at=timezone.now(),
                )
                charges.mark_paid(fee, payment, origin="provider", by=system)
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

        return {"people": len(people), "charges": n_charges, "consents": n_consents}
