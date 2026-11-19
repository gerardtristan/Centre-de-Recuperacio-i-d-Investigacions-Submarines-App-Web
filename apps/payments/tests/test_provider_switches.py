"""Configuració del proveïdor editable des de l'app (P-131, 095; VC-14, A7; P-196). Proveïdor fals,
sense xarxa. Només dades inventades."""

from datetime import timedelta

import pyotp
import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.accounts import totp
from apps.accounts.models import TotpDevice
from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.core import business_settings
from apps.core.models import AuditEntry, OutgoingEmail, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.payments import attempts, checkout, preferences
from apps.payments.models import FeeMethod
from apps.payments.providers import enabled_capabilities, fake, switch_key
from apps.payments.tests.test_checkout import SITE, new_charge

pytestmark = pytest.mark.django_db
R = Role.Code
NOTE = "Bizum aturat mentre el banc revisa el contracte"
BIZUM = switch_key("bizum")
URL = reverse("administration:setting_detail", kwargs={"section": "payments", "key": BIZUM})


@pytest.fixture(autouse=True)
def site(settings):
    settings.PUBLIC_SITE_URL = SITE
    fake.reset()


@pytest.fixture
def admin(make_admin):  # noqa: F811
    return make_admin(R.ADMINISTRATOR, username="anna.admin")


def code_for(account):
    device = TotpDevice.objects.get(account=account)
    return pyotp.TOTP(totp.secret_of(device)).at(timezone.now() + timedelta(seconds=30))


def switch_off(method, admin):
    business_settings.change(switch_key(method), False, admin, NOTE)


def test_everything_starts_as_the_provider_declares():
    assert enabled_capabilities() == fake.FakeProvider().capabilities()


@pytest.mark.parametrize("method", ["card", "bizum", "tokenization"])
def test_a_switch_off_hides_only_that_method(admin, method):
    switch_off(method, admin)
    caps = enabled_capabilities()
    assert getattr(caps, method) is False
    others = {"card", "bizum", "tokenization"} - {method}
    assert all(getattr(caps, m) for m in others)


def test_the_note_is_required(admin):
    # P-131: nota obligatòria, també des del servei.
    with pytest.raises(ValidationError, match="Cal una nota"):
        business_settings.change(BIZUM, False, admin, "  ")
    assert business_settings.get(BIZUM) is True


class TestScreen:
    def post(self, client, account, **extra):
        data = {"value": "0", "note": NOTE, "code": code_for(account)} | extra
        return client.post(URL, data)

    def test_the_administrator_saves_with_totp_and_note(
        self,
        admin,
        make_admin,  # noqa: F811
        login_as,
        django_capture_on_commit_callbacks,
    ):
        treasurer = make_admin(R.TREASURER)
        treasurer.notification_email = "tresorer@example.org"
        treasurer.save()
        client = login_as(admin, AREA_ADMIN)
        assert 'autocomplete="one-time-code"' in client.get(URL).content.decode()
        with django_capture_on_commit_callbacks(execute=True):
            response = self.post(client, admin)
        assert response.status_code == 302
        assert business_settings.get(BIZUM) is False
        entry = AuditEntry.objects.get(action=business_settings.ACTION_CHANGED)
        assert (entry.field, entry.old_value, entry.new_value, entry.reason) == (
            BIZUM,
            True,
            False,
            NOTE,
        )
        sent = OutgoingEmail.objects.get(template=business_settings.EMAIL_TEMPLATE)
        assert sent.to_address == "tresorer@example.org"

    @pytest.mark.parametrize("extra", [{"code": "000000"}, {"code": ""}, {"note": ""}])
    def test_without_a_good_code_or_a_note_nothing_is_saved(self, admin, login_as, extra):
        response = self.post(login_as(admin, AREA_ADMIN), admin, **extra)
        assert response.status_code == 200
        if extra != {"code": ""}:  # el camp buit té l'error al camp, sense el bàner
            assert "No s'ha desat res." in response.content.decode()
        assert business_settings.get(BIZUM) is True
        assert not AuditEntry.objects.filter(action=business_settings.ACTION_CHANGED).exists()

    def test_the_treasurer_only_reads_it(self, make_admin, login_as):  # noqa: F811
        treasurer = make_admin(R.TREASURER)
        client = login_as(treasurer, AREA_ADMIN)
        assert client.get(URL).status_code == 200
        assert self.post(client, treasurer).status_code == 404
        assert business_settings.get(BIZUM) is True


class TestWhatTheMemberSees:
    @pytest.fixture
    def charge(self, personal_account):
        return new_charge(personal_account.person)

    def test_no_bizum_button_and_no_bizum_order(self, admin, charge, personal_account, login_as):
        switch_off("bizum", admin)
        page = login_as(personal_account, AREA_PERSONAL).get(
            reverse("payments:charge", args=[charge.pk])
        )
        html = page.content.decode()
        assert "Paga amb targeta" in html and "Paga amb Bizum" not in html
        with pytest.raises(attempts.MethodNotAllowed):
            checkout.start_payment(charge, "bizum", personal_account)

    def test_no_card_button_and_no_card_order(self, admin, charge, personal_account, login_as):
        switch_off("card", admin)
        page = login_as(personal_account, AREA_PERSONAL).get(
            reverse("payments:charge", args=[charge.pk])
        )
        assert "Paga amb targeta" not in page.content.decode()
        with pytest.raises(attempts.MethodNotAllowed):
            checkout.start_payment(charge, "card", personal_account)

    def test_no_saved_card_offered(self, admin):
        # P-196: el proveïdor la permet i el club la té activa.
        assert FeeMethod.SAVED_CARD in preferences.offered_methods()
        switch_off("tokenization", admin)
        assert FeeMethod.SAVED_CARD not in preferences.offered_methods()
