"""Ajustos del 01 (T-M01-32 i la seva ampliació; addenda de la 055 i ampliació de la 091):
VC-01 amb versions del preu i data d'entrada en vigor (RN-M01-45; CA-M01-35), VC-02 com a llista
(CA-M01-123), VC-03, VC-04 (CA-M01-37) i VC-53 (CA-M01-124). Permisos de la columna «Qui el
canvia» i registre de cada canvi. Només dades inventades."""

from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from apps.core import audit, business_settings
from apps.core.models import AuditEntry, OutgoingEmail, Setting
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import cards, fees
from apps.members import member_requests as mr
from apps.members import settings as values
from apps.members.models import AnnualFee, FeeReminder, MembershipType
from apps.members.tests.test_cards import add_fee, make_member, pay, personal  # noqa: F401
from apps.members.tests.test_fees_079 import paid_until
from apps.members.tests.test_member_requests import change_request
from apps.members.tests.test_member_requests import make_member as make_supporter
from apps.members.tests.test_roster import admin_client

pytestmark = pytest.mark.django_db

FULL_PRICE = "members.annual_fee_cents.full"
SUPPORTER_PRICE = "members.annual_fee_cents.supporter"


def full():
    return MembershipType.objects.get(code="full")


def set_value(key, value):
    """Valor de prova sense passar per la pantalla (el servei es prova a part)."""
    Setting.objects.filter(key=key).update(initial_value=value)


# --- Cel·les i permisos (columna «Qui el canvia» de l'addenda) ------------------------------


EDITORS = {
    FULL_PRICE: {"treasurer", "administrator"},
    SUPPORTER_PRICE: {"treasurer", "administrator"},
    values.FEE_REMINDER_OFFSETS: {"treasurer"},
    values.SUPPLEMENT_DUE_DAYS: {"treasurer"},
    values.CARD_BACK_TEXT: {"secretary", "administrator"},
    values.CLASSIC_MEMBER_YEARS: {"administrator"},
    # T-M01-49 (097, P-61; P-396): com el preu de la quota.
    values.INSTALMENTS_ENABLED: {"treasurer", "administrator"},
    values.INSTALMENTS_TOTAL: {"treasurer", "administrator"},
    values.INSTALMENTS_SURCHARGE: {"treasurer", "administrator"},
    values.INSTALMENTS_UNPAID_DAYS: {"treasurer", "administrator"},
    # T-M01-43e (P-399): com els dies dels recordatoris.
    values.RENEWAL_NOTICE_MONTHS: {"treasurer"},
}
ROLES = ["treasurer", "administrator", "secretary", "president", "board", "instructor"]


def test_the_01_values_are_settings_with_their_initial_values():
    initial = dict(Setting.objects.filter(module="members").values_list("key", "initial_value"))
    assert initial == {
        FULL_PRICE: 9000,
        SUPPORTER_PRICE: 3500,
        values.FEE_REMINDER_OFFSETS: [-15, -1, 0, 15, 30],
        values.SUPPLEMENT_DUE_DAYS: 7,
        values.CARD_BACK_TEXT: Setting.objects.get(key=values.CARD_BACK_TEXT).initial_value,
        values.CLASSIC_MEMBER_YEARS: 0,
        values.INSTALMENTS_ENABLED: False,  # T-M01-49: apagat
        values.INSTALMENTS_TOTAL: 9600,  # 3 × 32 €, provisional (097)
        values.INSTALMENTS_SURCHARGE: 0,  # provisional (097)
        values.INSTALMENTS_UNPAID_DAYS: 30,
        values.RENEWAL_NOTICE_MONTHS: 1,  # T-M01-43e (abans, l'entorn)
    }
    prices = Setting.objects.filter(key__in=[FULL_PRICE, SUPPORTER_PRICE])
    assert all(s.affects_money and s.effective_dated for s in prices)


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("key", list(EDITORS))
def test_only_the_roles_of_the_addenda_can_edit_each_value(make_admin, role, key):  # noqa: F811
    account = make_admin(role)
    setting = Setting.objects.get(key=key)
    assert business_settings.can_edit(account, setting) is (role in EDITORS[key])
    assert business_settings.can_view(account, "members") is (
        role in {"treasurer", "administrator", "secretary"}
    )


def test_a_role_that_only_sees_the_section_is_refused_and_logged(make_admin):  # noqa: F811
    with pytest.raises(Http404):
        business_settings.change(values.CLASSIC_MEMBER_YEARS, 25, make_admin("treasurer"))
    assert AuditEntry.objects.filter(action=business_settings.ACTION_DENIED).count() == 1
    assert not Setting.objects.get(key=values.CLASSIC_MEMBER_YEARS).versions.exists()


# --- VC-01: versions del preu (RN-M01-45; CA-M01-35) -----------------------------------------


def test_ca_m01_35_a_new_price_applies_from_its_date_and_leaves_issued_fees(make_admin):  # noqa: F811
    treasurer = make_admin("treasurer")
    treasurer.notification_email = "tresorer@example.org"
    treasurer.save()
    first = paid_until(date(2027, 3, 10))
    second = paid_until(date(2027, 6, 10), first="Berta", number=1288, document="87654321X")
    (old,) = fees.generate_due_fees(date(2027, 2, 23))

    business_settings.change(
        FULL_PRICE, 9500, treasurer, "Assemblea de prova", effective_from=date(2027, 4, 1)
    )

    assert values.annual_fee_cents(full(), date(2027, 3, 31)) == 9000
    assert values.annual_fee_cents(full(), date(2027, 4, 1)) == 9500
    (new,) = fees.generate_due_fees(date(2027, 5, 26))
    old.charge.refresh_from_db()
    assert (old.member, old.charge.amount_cents) == (first, 9000)
    assert (new.member, new.charge.amount_cents) == (second, 9500)
    assert full().annual_fee_cents == 9000  # el tipus conserva el preu inicial
    email = OutgoingEmail.objects.get(template=business_settings.EMAIL_TEMPLATE)
    assert email.to_address == "tresorer@example.org"
    assert "90,00 €" in email.body_text and "95,00 €" in email.body_text
    entry = AuditEntry.objects.get(action=business_settings.ACTION_CHANGED)
    assert (entry.old_value, entry.new_value) == (9000, 9500)
    assert entry.reason == "Assemblea de prova"


def test_a_price_change_needs_a_date_and_a_note(make_admin):  # noqa: F811
    admin = make_admin("administrator")
    tomorrow = timezone.localdate() + timedelta(days=1)
    with pytest.raises(ValidationError):
        business_settings.change(SUPPORTER_PRICE, 4000, admin, "", effective_from=tomorrow)
    with pytest.raises(ValidationError):
        business_settings.change(SUPPORTER_PRICE, 4000, admin, "Prova", effective_from=None)
    with pytest.raises(ValidationError):
        business_settings.change(SUPPORTER_PRICE, 0, admin, "Prova", effective_from=tomorrow)
    assert not Setting.objects.get(key=SUPPORTER_PRICE).versions.exists()


def test_the_join_preview_and_the_supplement_read_the_price_in_force(make_admin):  # noqa: F811
    business_settings.change(
        FULL_PRICE, 9500, make_admin("treasurer"), "Prova", effective_from=timezone.localdate()
    )
    member = make_supporter()
    assert fees.supplement_cents(member, full()) == 6000  # 95 € - 35 €


# --- VC-02: llista de recordatoris (CA-M01-123) ----------------------------------------------


def test_ca_m01_123_reminders_follow_the_list(make_admin):  # noqa: F811
    business_settings.change(values.FEE_REMINDER_OFFSETS, [-10, 0, 20], make_admin("treasurer"))
    member = paid_until(date(2027, 3, 10))
    assert fees.generate_due_fees(date(2027, 2, 27)) == []  # 11 dies abans: encara no
    (fee,) = fees.generate_due_fees(date(2027, 2, 28))
    for day in (date(2027, 2, 28), date(2027, 3, 10), date(2027, 3, 30)):
        assert fees.send_due_reminders(day) == 1
    assert list(FeeReminder.objects.filter(fee=fee).values_list("offset_days", flat=True)) == [
        -10,
        0,
        20,
    ]
    assert fee.member == member


@pytest.mark.parametrize("value", [[], [-10, 91], [-10, -10], list(range(11))])
def test_ca_m01_123_an_invalid_list_is_rejected_and_nothing_saved(make_admin, value):  # noqa: F811
    with pytest.raises(ValidationError):
        business_settings.change(values.FEE_REMINDER_OFFSETS, value, make_admin("treasurer"))
    assert values.fee_reminder_offsets() == [-15, -1, 0, 15, 30]
    assert not AuditEntry.objects.filter(action=business_settings.ACTION_CHANGED).exists()


# --- VC-53: venciment del suplement (CA-M01-124) ---------------------------------------------


def test_ca_m01_124_the_supplement_is_due_after_the_days_in_force(make_admin):  # noqa: F811
    secretary = make_admin("secretary")
    before = mr.approve_type_change(change_request(make_supporter("Abans")), by=secretary)
    business_settings.change(values.SUPPLEMENT_DUE_DAYS, 10, make_admin("treasurer"))
    request = change_request(make_supporter("Despres"))
    client = admin_client(secretary)
    page = client.get(reverse("administration:member_request_detail", args=[request.pk]))
    assert "10 dies" in page.content.decode()
    after = mr.approve_type_change(request, by=secretary)
    today = timezone.localdate()
    assert after.due_on == today + timedelta(days=10)
    before.refresh_from_db()
    assert before.due_on == today + timedelta(days=7)
    assert AnnualFee.objects.count() == 2


# --- VC-03 i VC-04: darrere del carnet i insígnia de soci clàssic (CA-M01-37) ----------------


@pytest.mark.parametrize(("years", "badge"), [(0, False), (25, False), (7, True)])
def test_ca_m01_37_the_card_shows_the_badge_from_the_threshold(personal, years, badge):  # noqa: F811
    set_value(values.CLASSIC_MEMBER_YEARS, years)
    set_value(values.CARD_BACK_TEXT, "Text del darrere de prova.")
    member = make_member(joined_on=timezone.localdate().replace(year=2019, day=1))
    pay(add_fee(member, period=timezone.localdate().year))
    cards.issue_card(member, by=audit.system("proves"))
    html = personal(member).get(reverse("members:card")).content.decode()
    assert ("Soci clàssic" in html) is badge
    assert "Text del darrere de prova." in html
    assert "Carnet personal i intransferible" not in html


# --- Revisió de la PR #211 ---------------------------------------------------------------


@pytest.mark.parametrize(("months", "value", "ok"), [(1, [-28, 0], True), (1, [-29, 0], False),
                                                     (2, [-45, 0], True)])  # fmt: skip
def test_p_360_reminders_cannot_start_before_the_renewal_notice(
    make_admin,  # noqa: F811
    settings,
    months,
    value,
    ok,
):
    # P-360, opció B: la quota es genera el dia del primer recordatori i l'avís de renovació
    # (T-M01-43) ha de sortir abans; un mes en té com a mínim 28 dies.
    treasurer = make_admin("treasurer")
    Setting.objects.filter(key=values.RENEWAL_NOTICE_MONTHS).update(initial_value=months)
    if ok:
        business_settings.change(values.FEE_REMINDER_OFFSETS, value, treasurer)
        assert values.fee_reminder_offsets() == value
    else:
        with pytest.raises(ValidationError, match="avís de renovació"):
            business_settings.change(values.FEE_REMINDER_OFFSETS, value, treasurer)
        assert values.fee_reminder_offsets() == [-15, -1, 0, 15, 30]


def test_the_renewal_fee_takes_the_price_in_force_when_it_is_generated(make_admin):  # noqa: F811
    # RN-M01-13 i CA-M01-35: el preu vigent el dia de generar la quota, encara que el preu nou
    # entri en vigor abans del venciment.
    paid_until(date(2027, 3, 10))
    business_settings.change(
        FULL_PRICE, 9500, make_admin("treasurer"), "Prova", effective_from=date(2027, 3, 1)
    )
    (fee,) = fees.generate_due_fees(date(2027, 2, 23))  # el preu nou comença l'1 de març
    assert (fee.due_on, fee.charge.amount_cents) == (date(2027, 3, 10), 9000)


def test_every_01_setting_has_an_edit_permission_in_the_catalog():
    # Cap ajust que ningú no pugui editar pel seu permís (només hi ha preus dels dos tipus).
    from apps.core.permission_catalog import CATALOG

    keys = Setting.objects.filter(module="members").values_list("key", flat=True)
    assert all(business_settings.permission_code(key) in CATALOG for key in keys)


def test_an_approximate_join_date_never_gets_the_badge(personal):  # noqa: F811
    # RN-M01-23 (text original): la insígnia només si la data d'alta no és aproximada.
    set_value(values.CLASSIC_MEMBER_YEARS, 5)
    member = make_member(joined_on=date(2001, 1, 1), joined_on_is_approximate=True)
    pay(add_fee(member, period=timezone.localdate().year))
    cards.issue_card(member, by=audit.system("proves"))
    html = personal(member).get(reverse("members:card")).content.decode()
    assert "Soci clàssic" not in html


def test_the_cluber_import_matches_the_price_in_force_on_the_renewal_date(make_admin):  # noqa: F811
    from apps.members.imports import cluber
    from apps.members.tests.test_cluber_preview import build, only_row, record

    start = timezone.localdate() + timedelta(days=10)
    business_settings.change(SUPPORTER_PRICE, 4000, make_admin("treasurer"), "Prova",
                             effective_from=start)  # fmt: skip
    after = (start + timedelta(days=1)).strftime("%d/%m/%Y")
    before = (start - timedelta(days=1)).strftime("%d/%m/%Y")
    cells = {"Quota": "Quota anual 40€", "Preu total": "40", "Data alta/renovació": after}
    row = only_row(cluber.preview(build([record(1, cells)])))
    assert (row.member_type, row.member_type_by) == ("supporter", "price")
    assert "total_price_differs" not in row.warnings
    cells["Data alta/renovació"] = before
    row = only_row(cluber.preview(build([record(1, cells)])))
    assert row.member_type is None and "member_type" in row.pending
