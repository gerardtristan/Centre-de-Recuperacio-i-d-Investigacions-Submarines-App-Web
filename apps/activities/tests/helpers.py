"""Dades inventades per a les proves del mòdul 02: una fitxa, un curs i una sortida.

Les dates són fixes i els serveis reben `today` i `now`: cap prova depèn del dia que s'executa.
"""

import datetime
import itertools

from django.utils import timezone

from apps.activities import catalogue, services
from apps.activities.models import OutingType, TrainingCatalogueEntry
from apps.core.models import Department, Person

TODAY = datetime.date(2027, 5, 3)
STARTS = datetime.date(2027, 6, 14)
ENDS = datetime.date(2027, 6, 15)
REASON = "Motiu inventat de proves"
_numbers = itertools.count(1)


def at(year, month, day, hour=0, minute=0) -> datetime.datetime:
    """Un moment amb fus horari (el del projecte)."""
    return timezone.make_aware(datetime.datetime(year, month, day, hour, minute))


CLOSES = at(2027, 6, 10, 20)  # data límit d'inscripció: quatre dies abans de l'inici
BEFORE_DEADLINE = at(2027, 6, 1, 9)
AFTER_DEADLINE = at(2027, 6, 11, 9)


def general() -> Department:
    return Department.objects.get(name=Department.GENERAL)


def a_person(first_name="Responsable") -> Person:
    return Person.objects.create(
        first_name=first_name, last_name="Prova", origin=Person.Origin.IN_PERSON
    )


def an_entry(by, **fields) -> TrainingCatalogueEntry:
    data = {
        "kind": TrainingCatalogueEntry.Kind.COURSE,
        "name": f"Curs inventat de proves {next(_numbers)}",
        "default_places": 8,
        "price_member_cents": 4500,
        "price_non_member_cents": 6000,
        "department": general(),
        **fields,
    }
    return catalogue.create_entry(by=by, today=TODAY, **data)


def common_data(**fields) -> dict:
    data = {
        "title": "Activitat inventada de proves",
        "starts_on": STARTS,
        "ends_on": ENDS,
        "registration_closes_at": CLOSES,
        **fields,
    }
    if "responsible" not in data:
        data["responsible"] = a_person()
    return data


def a_course(by, entry=None, **fields):
    entry = entry or an_entry(by)
    return services.create_course(
        by=by, catalogue_entry=entry, today=TODAY, **common_data(**fields)
    )


def outing_type(name="Immersió") -> OutingType:
    return OutingType.objects.get(name=name)


def an_outing(by, **fields):
    classification = {
        "outing_type": fields.pop("outing_type", None) or outing_type(),
        "subtype": fields.pop("subtype", None),
        "project": fields.pop("project", None),
    }
    data = {"max_places": 12, "price_member_cents": 4500, "price_non_member_cents": 6000, **fields}
    return services.create_outing(by=by, today=TODAY, **classification, **common_data(**data))


def client_for(account):
    """Un client amb la sessió de l'àrea que toca al compte, com si hagués entrat (amb TOTP)."""
    import time

    from django.test import Client

    from apps.accounts.models import Account
    from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
    from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY

    client = Client()
    client.force_login(account)
    session = client.session
    session[AREA_SESSION_KEY] = (
        AREA_PERSONAL if account.kind == Account.Kind.PERSONAL else AREA_ADMIN
    )
    session[AUTH_AT_SESSION_KEY] = time.time()
    session.save()
    return client


def admin_with_mail(make_admin, role, address):
    """Un compte d'administrador amb correu de notificació (els avisos només van a qui en té)."""
    account = make_admin(role)
    account.notification_email = address
    account.save()
    return account


def a_done_environmental_outing(by, **fields):
    """Una sortida de medi ambient (subtipus «Neteja») que ja s'ha fet."""
    from apps.activities.models import Activity, EnvironmentalSubtype

    outing = an_outing(
        by,
        outing_type=outing_type("Medi ambient"),
        subtype=EnvironmentalSubtype.objects.get(name="Neteja"),
        **fields,
    )
    Activity.objects.filter(pk=outing.pk).update(status=Activity.Status.DONE)
    outing.refresh_from_db()
    return outing


# --- Inscripcions (T-M02-11 i següents) ----------------------------------------------------------

PUBLISHED = at(2027, 5, 20, 9)  # abans de BEFORE_DEADLINE
_member_numbers = itertools.count(9001)


def a_member(first="Sòcia", *, status="active", account=True):
    """Una persona sòcia inventada, amb el compte personal actiu. Torna el compte (o la persona,
    si `account=False`)."""
    from apps.members.models import Member, MembershipType

    number = next(_member_numbers)
    person = Person.objects.create(first_name=first, last_name="Prova", origin=Person.Origin.WEB)
    Member.objects.create(
        person=person,
        member_number=number,
        type=MembershipType.objects.get(code="full"),
        status=status,
        joined_on=datetime.date(2019, 3, 12),
    )
    if not account:
        return person
    return a_personal_account(person, f"soci{number}@example.org")


def a_personal_account(person=None, email=None):
    """Un compte personal actiu d'una persona que no és sòcia (o de la que es doni)."""
    from apps.accounts.models import Account

    person = person or a_person("Convidada")
    email = email or f"persona{next(_numbers)}@example.org"
    account = Account.objects.create_personal(person, email)
    account.status = Account.Status.ACTIVE
    account.save()
    return account


def an_open_outing(by, **fields):
    """Una sortida publicada, amb les inscripcions obertes fins a `CLOSES`."""
    from apps.activities import states

    outing = an_outing(by, **fields)
    states.publish(outing, by=by, now=PUBLISHED)
    outing.refresh_from_db()
    return outing


def an_open_course(by, entry=None, **fields):
    from apps.activities import states

    course = a_course(by, entry, **fields)
    states.publish(course, by=by, now=PUBLISHED)
    course.refresh_from_db()
    return course


def pay(charge):
    """Pagament confirmat pel proveïdor (mode de proves), amb el servei real de la 00. No avisa
    el 02: això ho fa l'esdeveniment `charge.paid` (T-M05b-21)."""
    from apps.core import audit, charges
    from apps.core.models import Payment

    payment = Payment.objects.create(
        charge=charge,
        method=Payment.Method.CARD,
        amount_cents=charge.amount_cents,
        provider_status="prova",
        provider_reference=f"PROVA-{charge.pk}",
        paid_at=timezone.now(),
    )
    charges.mark_paid(charge, payment, origin="provider", by=audit.system("proves"))
    charge.refresh_from_db()
    return payment
