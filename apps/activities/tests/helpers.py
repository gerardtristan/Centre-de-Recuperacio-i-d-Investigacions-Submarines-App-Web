"""Dades inventades per a les proves del 02: les files directes (`outing_data`) i les que passen
pels serveis (`a_course`, `an_outing`, `a_place`…)."""

import datetime
import itertools

from django.utils import timezone

from apps.activities import catalogue, services
from apps.activities.models import (
    Activity,
    EnvironmentalProject,
    EnvironmentalSubtype,
    OutingType,
    TrainingCatalogueEntry,
)
from apps.core.models import AuditEntry, Department, Person

START = datetime.date(2027, 6, 14)
_numbers = itertools.count(1)


def outing_data(default_place, **fields):
    data = {
        "kind": Activity.Kind.OUTING,
        "title": "Sortida inventada",
        "outing_type": OutingType.objects.get(name="Immersió"),
        "department": Department.objects.get(name=Department.GENERAL),
        "starts_on": START,
        "ends_on": START,
        "place": default_place,
        "max_places": 12,
        "registration_closes_at": timezone.make_aware(datetime.datetime(2027, 6, 10, 20)),
        "payment_window_hours": 72,
        "price_member_cents": 4500,
        "price_non_member_cents": 6000,
        "responsible": Person.objects.create(first_name="Responsable", origin="in_person"),
    }
    return {**data, **fields}


def at(hour):
    return timezone.make_aware(datetime.datetime.combine(START, datetime.time(hour)))


TODAY = datetime.date(2027, 5, 3)
NEXT_MONTH = datetime.date(2027, 6, 1)
STARTS, ENDS = datetime.date(2027, 6, 14), datetime.date(2027, 6, 15)
REASON = "Motiu inventat de proves"
S = Activity.Status


def moment(year, month, day, hour=0, minute=0):
    return timezone.make_aware(datetime.datetime(year, month, day, hour, minute))


CLOSES = moment(2027, 6, 10, 20)


def general():
    return Department.objects.get(name=Department.GENERAL)


def a_person(first_name="Responsable"):
    return Person.objects.create(first_name=first_name, last_name="Prova", origin="in_person")


def an_entry(manager, **fields):
    data = {
        "kind": TrainingCatalogueEntry.Kind.COURSE,
        "name": f"Curs inventat {next(_numbers)}",
        "default_places": 8,
        "price_member_cents": 4500,
        "price_non_member_cents": 6000,
        "department": general(),
        **fields,
    }
    return catalogue.create_entry(by=manager, today=TODAY, **data)


def a_place(manager, prices=(4500, 6000)):
    place = catalogue.create_place(by=manager, name=f"Lloc inventat {next(_numbers)}")
    if prices:
        catalogue.change_place_price(
            place,
            by=manager,
            price_member_cents=prices[0],
            price_non_member_cents=prices[1],
            valid_from=TODAY,
            note="Preu inicial inventat.",
            today=TODAY,
        )
    return place


def common_data(**fields):
    data = {
        "title": "Activitat inventada de proves",
        "starts_on": STARTS,
        "ends_on": ENDS,
        "registration_closes_at": CLOSES,
        **fields,
    }
    data.setdefault("responsible", a_person())
    return data


def a_course(manager, entry=None, **fields):
    entry = entry or an_entry(manager)
    return services.create_course(
        by=manager, catalogue_entry=entry, today=TODAY, **common_data(**fields)
    )


def outing_type(name="Immersió"):
    return OutingType.objects.get(name=name)


def an_outing(manager, **fields):
    classification = {
        "outing_type": fields.pop("outing_type", None) or outing_type(),
        "subtype": fields.pop("subtype", None),
        "project": fields.pop("project", None),
    }
    if "place" not in fields:
        fields["place"] = a_place(manager)
    data = {"max_places": 12, **fields}
    return services.create_outing(by=manager, today=TODAY, **classification, **common_data(**data))


def entries_of(activity, action):
    return AuditEntry.objects.filter(
        action=action, target_type="activities.activity", target_id=str(activity.pk)
    )


def raise_price(manager, entry, valid_from):
    return catalogue.change_prices(
        entry,
        by=manager,
        price_member_cents=5000,
        price_non_member_cents=6500,
        valid_from=valid_from,
        note="Puja el preu (nota inventada).",
        today=TODAY,
    )


def cleaning():
    return EnvironmentalSubtype.objects.get(name="Neteja")


def a_project():
    return EnvironmentalProject.objects.create(
        name=f"Projecte inventat {next(_numbers)}", objective="Objectiu.", department=general()
    )
