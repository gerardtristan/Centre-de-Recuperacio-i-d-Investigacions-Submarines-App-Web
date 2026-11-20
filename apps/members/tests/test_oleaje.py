"""Oleaje (T-DX-17) i l'inici del soci (T-DX-60): la portada de l'àrea de socis mostra l'estat de la
quota, el carnet, els pendents, els pagaments recents, la història i la llicència, només del soci de
la sessió i només al compte personal. El compte enrere de la quota només surt des del primer dia
d'avís (VC-02) i la insígnia de soci clàssic segueix el llindar VC-04."""

from datetime import date

import pytest
from django.urls import reverse

from apps.accounts.models import Account
from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.core.models import Person, Setting
from apps.members import settings as values
from apps.members.fee_rules import local_today
from apps.members.models import Member, MembershipType
from apps.members.tests.test_cards import account_for, add_fee, make_member, paid_member
from conftest import PASSWORD

pytestmark = pytest.mark.django_db
HOME = "core:home"


def summary(html):
    return (
        html.split('class="inici-quota"', 1)[1].split("</section>", 1)[0]
        if "inici-quota" in html
        else None
    )


def home(login_as, member, email="anna.soci@example.org"):
    account = account_for(member, email)
    return login_as(account, AREA_PERSONAL).get(reverse(HOME)).content.decode()


def setting(key, value):
    Setting.objects.filter(key=key).update(initial_value=value)


def test_a_paid_member_is_up_to_date_without_countdown_far_from_renewal(login_as):
    html = home(login_as, paid_member())
    assert "oleaje-portada" in html
    block = summary(html)
    assert "Al dia" in block and "Es renova el" in block and "vigencia" not in block
    assert reverse("members:card") in block and reverse("members:fees") in block
    assert block.count("boto-principal") == 1  # D19: «El meu carnet»
    assert "franja-estat" not in html  # cap pendent


def test_the_countdown_appears_inside_the_first_reminder_window(login_as):
    setting(values.FEE_REMINDER_OFFSETS, [-400, 0])  # VC-02: el primer avís, 400 dies abans
    assert "vigencia" in summary(home(login_as, paid_member()))


def test_a_pending_fee_shows_pending_the_strip_and_no_countdown(login_as):
    member = make_member()
    fee = add_fee(member)
    html = home(login_as, member)
    block = summary(html)
    assert "Pendent" in block and "vigencia" not in block
    strip = html.split('class="avis avis-avis franja-estat"', 1)[1].split("</div>", 1)[0]
    assert "1 pagament pendent" in strip and "Quota 2026" in strip and "90,00" in strip
    assert reverse("payments:charge", args=[fee.charge_id]) in strip
    assert "Encara no has fet cap pagament." in html


def test_a_pending_fee_not_yet_due_without_card_makes_pay_now_the_main_action(login_as):
    """V20: la quota pendent que encara no ha vençut surt com a pendent, amb l'import i el
    venciment (no «—»); sense carnet, el botó principal
    és «Paga ara», al costat de l'import (D19)."""
    member = make_member()
    fee = add_fee(member, period=local_today().year + 1)
    html = home(login_as, member)
    block = summary(html)
    assert "Pendent" in block and "90,00" in block and "venç el 01/01/" in block
    assert block.count("boto-principal") == 1 and reverse("members:card") not in block
    assert reverse("payments:charge", args=[fee.charge_id]) in block
    strip = html.split('class="avis avis-avis franja-estat"', 1)[1].split("</div>", 1)[0]
    assert "boto-principal" not in strip


def test_recent_payments_history_and_licence(login_as):
    member = paid_member()
    setting(values.CLASSIC_MEMBER_YEARS, 5)  # VC-04; alta el 2019
    html = home(login_as, member)
    assert "Pagaments recents" in html and "Quota 2026" in html
    assert "Soci des de 2019 (7 anys)" in html and "Soci clàssic" in html
    assert "No hi ha cap llicència registrada." in html


def test_no_classic_badge_below_the_threshold_or_with_an_approximate_date(login_as):
    setting(values.CLASSIC_MEMBER_YEARS, 5)
    member = paid_member(joined_on=date(2019, 3, 12), joined_on_is_approximate=True)
    html = home(login_as, member)
    assert "Soci des de ~2019" in html and "Soci clàssic" not in html
    setting(values.CLASSIC_MEMBER_YEARS, 30)
    berta = paid_member("Berta", 1300, document="00000000T")
    assert "Soci clàssic" not in home(login_as, berta, "berta.soci@example.org")


def test_only_the_session_member_is_shown(login_as):
    paid_member("Berta", number=1300, document="00000000T")
    html = login_as(account_for(make_member()), AREA_PERSONAL).get(reverse(HOME)).content.decode()
    assert "Berta" not in html and "1300" not in html


def test_a_person_who_is_not_a_member_gets_no_summary(login_as):
    person = Person.objects.create(
        first_name="Convidat", last_name="Prova", origin=Person.Origin.WEB
    )
    account = Account.objects.create_personal(person, "convidat@example.org", PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    html = login_as(account, AREA_PERSONAL).get(reverse(HOME)).content.decode()
    assert "oleaje-portada" in html and summary(html) is None
    assert "inici-graella" not in html and "franja-estat" not in html


def test_the_admin_account_gets_no_member_summary(login_as, admin_account):
    Member.objects.create(
        person=admin_account.person,
        member_number=1400,
        type=MembershipType.objects.get(code="full"),
        status=Member.Status.ACTIVE,
        joined_on=date(2019, 3, 12),
    )
    html = login_as(admin_account, AREA_ADMIN).get(reverse(HOME)).content.decode()
    assert summary(html) is None and "1400" not in html and "inici-graella" not in html
