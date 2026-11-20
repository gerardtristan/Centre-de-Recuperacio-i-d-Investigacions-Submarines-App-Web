"""Dades inventades per a les proves del 02."""

import datetime

from django.utils import timezone

from apps.activities.models import Activity, OutingType
from apps.core.models import Department, Person

START = datetime.date(2027, 6, 14)


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
