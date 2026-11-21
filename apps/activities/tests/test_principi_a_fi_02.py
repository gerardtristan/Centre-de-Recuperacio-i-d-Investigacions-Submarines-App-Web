"""Prova de flux sencer de la llesca F2-2 (T-M02-26; decisió 092: proveïdor fictici). El
responsable crea una sortida en un lloc amb preu estàndard i la publica; com que demana llicència,
un soci en treu una d'un dia (opció encesa a la prova), la paga, la secretaria la deixa vigent i
el soci s'inscriu sense cap avís; un convidat s'hi inscriu amb «Soc major d'edat» i rep l'avís
de requisits. Tots dos paguen pel 05b amb el proveïdor fictici, `charge.paid` confirma les
inscripcions i el dia de la sortida es passa llista. Només dades inventades."""

import datetime

import pytest
from django.utils import timezone

from apps.activities import attendance, catalogue, enrolment, guests, services, states
from apps.activities.models import Attendance, Enrolment, OutingType
from apps.core import business_settings, events
from apps.core.models import Charge, Event, GuestLink, LegalText, Person, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.licences import filing, prices
from apps.licences import services as licences
from apps.licences.models import LicenceType, ValidityRule
from apps.payments.providers import fake
from apps.payments.tests.test_principi_a_fi import pay_by_provider

from .helpers import a_member

R = Role.Code
S = Enrolment.Status


@pytest.fixture(autouse=True)
def fake_provider(settings):
    settings.PUBLIC_SITE_URL = "https://socis.example.org"
    fake.reset()
    yield
    fake.reset()


@pytest.fixture
def day_enabled(monkeypatch):
    real = business_settings.get
    monkeypatch.setattr(
        business_settings, "get",
        lambda key, at=None: True if key == licences.DAY_ENABLED else real(key, at),
    )  # fmt: skip


def deliver_all():
    for event in Event.objects.order_by("pk"):
        events.deliver(event.pk)


def at(day, hour):
    return timezone.make_aware(datetime.datetime.combine(day, datetime.time(hour)))


@pytest.mark.django_db
def test_f2_2_outing_enrol_member_and_guest_pay_confirm_and_roll(make_admin, day_enabled):  # noqa: F811
    today = timezone.localdate()
    day = today + datetime.timedelta(days=30)
    manager, secretary = make_admin(R.COURSES_MANAGER), make_admin(R.SECRETARY)
    for kind, content in (
        ("privacy", "Política inventada."),
        (guests.ADULT, guests.ADULT_PROPOSAL),
    ):
        LegalText.objects.get_or_create(kind=kind, version=1, defaults={"content": content})

    # 1. Un lloc amb preu estàndard i una sortida que en pren el preu, publicada.
    cove = catalogue.create_place(by=manager, name="Cala inventada")
    catalogue.change_place_price(
        cove, by=manager, price_member_cents=4500, price_non_member_cents=6000,
        valid_from=today, note="Preu inventat.", today=today,
    )  # fmt: skip
    outing = services.create_outing(
        by=manager, outing_type=OutingType.objects.get(name="Immersió"), today=today,
        title="Sortida inventada", starts_on=day, ends_on=day,
        registration_closes_at=at(day - datetime.timedelta(days=3), 20), place=cove,
        max_places=10, open_to_non_members=True, licence_required=True,
        requirements_mode="warn", responsible=manager.person,
    )  # fmt: skip
    assert (outing.price_member_cents, outing.price_non_member_cents) == (4500, 6000)
    states.publish(outing, by=manager)
    outing.refresh_from_db()

    # 2. La sortida demana llicència: el soci en treu una d'un dia, la paga i queda vigent.
    member = a_member("Marta")
    day_type = LicenceType.objects.create(
        name="Un dia (inventat)", category=LicenceType.Category.AMATEUR,
        validity_rule=ValidityRule.SINGLE_DAY,
    )  # fmt: skip
    prices.add_price(
        day_type, federation_cost_cents=1500, non_member_surcharge_cents=500,
        valid_from=today, note="Tarifa inventada", actor=secretary,
    )  # fmt: skip
    licence = licences.request(member.person, day_type, day, actor=member)
    assert pay_by_provider(licence.charge, "card", member).status == "paid"
    deliver_all()
    licence.refresh_from_db()
    filing.mark_active(licence, "F-0001", actor=secretary)

    # 3. El soci s'inscriu (sense avís) i el convidat, amb «Soc major d'edat» (amb avís).
    own = enrolment.enrol(outing, member.person, channel="account", actor=member)
    guest = guests.enrol_guest(
        outing, {"first_name": "Mar", "last_name": "Convidada",
                 "contact_email": "mar@example.org", "accept_privacy": True,
                 "adult_declared": True},
    )  # fmt: skip
    assert (own.status, own.price_cents, own.requirements_warning) == (S.PENDING_PAYMENT, 4500, "")
    assert (guest.status, guest.price_cents) == (S.PENDING_PAYMENT, 6000)
    assert guest.requirements_warning  # sense llicència: avís, el mode és «avís»
    assert Person.objects.get(pk=guest.person_id).origin == Person.Origin.GUEST

    # 4. Cobrament pel 05b amb el proveïdor fictici: el soci amb el seu compte i el convidat amb
    # el seu enllaç. `charge.paid` confirma les dues inscripcions.
    assert pay_by_provider(own.charge, "card", member).status == "paid"
    link = GuestLink.objects.get(charge=guest.charge)
    assert pay_by_provider(guest.charge, "card", link).status == "paid"
    deliver_all()
    for row in (own, guest):
        row.refresh_from_db()
        assert (row.status, row.charge.status) == (S.CONFIRMED, Charge.Status.PAID)

    # 5. El dia de la sortida, la llista porta els dos confirmats i es passa.
    roll = attendance.roll(outing, viewer=manager, today=day)
    assert {row.enrolment_id for row in roll.rows} == {own.pk, guest.pk}
    assert {row.enrolment_id: row.licence_valid for row in roll.rows} == {
        own.pk: True, guest.pk: False,
    }  # fmt: skip
    attendance.mark(own, None, present=True, by=manager, today=day)
    attendance.mark(guest, None, present=False, by=manager, today=day)
    marks = Attendance.objects.filter(enrolment__activity=outing)
    assert dict(marks.values_list("enrolment", "present")) == {
        own.pk: True, guest.pk: False,
    }  # fmt: skip
