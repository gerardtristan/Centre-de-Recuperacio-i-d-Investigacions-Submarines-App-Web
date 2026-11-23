"""Prova de flux sencer de la llesca F2-1 (T-M06-17; decisió 092: proveïdor fictici). Un soci
demana la llicència, la paga amb targeta pel proveïdor fictici, la secretaria la tramita i la
deixa vigent, la fitxa del soci la mostra (còpia del 01), surt a l'avís de venciment de 60 dies i
el soci renova la de l'any vinent, que atura els avisos de l'anterior. Només dades inventades."""

import datetime

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.core import events
from apps.core.models import Charge, Event, OutgoingEmail, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.licences import filing, prices, reminders, services
from apps.licences.models import Licence
from apps.members.services import licence_record
from apps.payments.providers import fake
from apps.payments.tests.test_principi_a_fi import pay_by_provider

D = datetime.date
R = Role.Code


@pytest.fixture(autouse=True)
def fake_provider(settings):
    settings.PUBLIC_SITE_URL = "https://socis.example.org"
    fake.reset()
    yield
    fake.reset()


def deliver_all():
    for event in Event.objects.order_by("pk"):
        events.deliver(event.pk)


@pytest.mark.django_db
def test_f2_1_request_pay_file_activate_remind_and_renew(
    make_admin,  # noqa: F811
    price_setter,
    annual,
    login_as,
):
    from apps.accounts.models import Account
    from apps.members.tests.test_cards import make_member

    secretary = make_admin(R.SECRETARY)
    secretary.notification_email = "secretaria@example.org"
    secretary.save()
    member = make_member("Marta", number=77, document="00000077Z")
    login = Account.objects.create_personal(member.person, "marta@example.org",
                                            "contrasenya-de-proves-1954")  # fmt: skip
    login.status = Account.Status.ACTIVE
    login.save()
    prices.add_price(
        annual, federation_cost_cents=9000, non_member_surcharge_cents=2000,
        valid_from=D(2020, 1, 1), note="Tarifa inventada", actor=price_setter,
    )  # fmt: skip

    # 1. Demanar-la (soci) i pagar-la amb targeta pel proveïdor fictici.
    licence = services.request(member.person, annual, actor=login)
    attempt = pay_by_provider(licence.charge, "card", login)
    assert attempt.status == "paid"
    deliver_all()  # charge.paid → llicència pagada i avís a qui tramita
    licence.refresh_from_db()
    assert (licence.status, licence.charge.status) == ("paid", Charge.Status.PAID)
    assert OutgoingEmail.objects.filter(template="avis-llicencia-pagada").count() == 1

    # 2. Tramitar-la i deixar-la vigent amb el número federatiu.
    filing.mark_filed(licence, actor=secretary)
    licence = filing.mark_active(licence, "F-0077", actor=secretary)
    deliver_all()  # licence.issued → còpia del 01
    copy = licence_record(member.person)
    assert (copy.licence_type, copy.expires_on) == (annual.name, licence.expires_on)
    html = (
        login_as(secretary, AREA_ADMIN)
        .get(reverse("administration:member_detail", args=[member.pk]))
        .content.decode()
    )
    assert annual.name in html and licence.expires_on.strftime("%d/%m/%Y") in html

    # 3. L'avís de venciment de 60 dies la troba.
    expiry = licence.expires_on
    assert reminders.due(expiry - datetime.timedelta(days=60))[60] == [licence]

    # 4. Renovar la de l'any vinent des de l'obertura; els avisos de l'anterior s'aturen.
    opening = D(expiry.year, 12, 1)
    renewal = services.request(member.person, annual, D(expiry.year + 1, 1, 1), actor=login,
                               today=opening)  # fmt: skip
    assert renewal.renewal_of == licence
    assert reminders.due(expiry - datetime.timedelta(days=30))[30] == []
    pay_by_provider(renewal.charge, "card", login)
    deliver_all()
    renewal.refresh_from_db()
    renewal = filing.mark_active(renewal, "F-0078", actor=secretary, today=opening)
    deliver_all()  # licence.renewed → la còpia del 01 la mostra
    assert Event.objects.filter(name=events.LICENCE_RENEWED, payload__licence=renewal.pk).exists()
    assert licence_record(member.person).expires_on == D(expiry.year + 1, 12, 31)
    assert Licence.objects.filter(person=member.person, status="active").count() == 2
