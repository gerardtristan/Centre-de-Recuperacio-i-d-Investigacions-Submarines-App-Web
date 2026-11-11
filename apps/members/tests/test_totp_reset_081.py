"""Restabliment presencial del doble factor d'un compte personal (P-52; decisió 081, punt 24;
RN-M01-104; T-M01-51).

M2 amb edició (i P4 per obrir la fitxa), comprovació de la identitat en persona amb el document
de la fitxa, motiu, codi TOTP nou de qui ho fa, registre, sessions tancades i avís al titular. Cap
camí per correu. Els comptes personals continuen sense codis de recuperació. Només dades
inventades.
"""

import pyotp
import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from apps.accounts import email_links, personal_reset, tokens
from apps.accounts.models import Account, RecoveryCode, TotpDevice
from apps.accounts.security import AREA_PERSONAL
from apps.accounts.tests.test_personal_totp import with_totp
from apps.core.models import AuditEntry, OutgoingEmail, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.tests.test_roster import DETAIL, admin_client, make_member
from conftest import PASSWORD

RESET = "administration:member_totp_reset"
DOCUMENT = "12345678Z"
NOTE = "Ha perdut el mòbil (motiu inventat)."

pytestmark = pytest.mark.django_db


def admin_code(account, offset=1):
    """Un codi nou de qui ho fa (no el mateix interval que l'entrada), amb el secret del seu
    dispositiu de proves."""
    from apps.accounts import totp

    secret = totp.secret_of(TotpDevice.objects.get(account=account))
    return pyotp.TOTP(secret).at(timezone.now(), counter_offset=offset)


@pytest.fixture
def soci(db):
    member = make_member(720, "Rita", "Mòbil", id_document_type="dni", id_document_number=DOCUMENT)
    account = Account.objects.create_personal(member.person, "rita@example.org", PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    with_totp(account)
    return member, account


@pytest.fixture
def secretary(make_admin):  # noqa: F811
    return make_admin("secretary")


def post(client, member, by, **overrides):
    data = {
        "document": DOCUMENT.lower(),
        "identity_checked": "on",
        "note": NOTE,
        "code": admin_code(by),
        **overrides,
    }
    return client.post(reverse(RESET, args=[member.pk]), data)


def test_detail_offers_it_only_with_m2(soci, secretary, make_admin):  # noqa: F811
    member = soci[0]
    link = reverse(RESET, args=[member.pk])
    assert link in admin_client(secretary).get(reverse(DETAIL, args=[member.pk])).content.decode()
    treasurer = admin_client(make_admin("treasurer"))
    assert link not in treasurer.get(reverse(DETAIL, args=[member.pk])).content.decode()
    assert treasurer.get(link).status_code in (403, 404)


def test_in_person_reset_removes_the_factor_closes_sessions_records_and_notifies(
    soci, secretary, login_as
):
    member, account = soci
    session = login_as(account, AREA_PERSONAL)
    assert session.get(reverse("members:profile")).status_code == 200
    response = post(admin_client(secretary), member, secretary)
    assert response.status_code in (302, 303)

    assert not TotpDevice.objects.filter(account=account).exists()
    assert not RecoveryCode.objects.filter(account=account).exists()
    assert session.get(reverse("members:profile")).status_code == 401  # sessions tancades
    entry = AuditEntry.objects.get(action=personal_reset.PERSONAL_TOTP_RESET)
    assert entry.actor_account == secretary and entry.target_id == str(account.pk)
    assert entry.reason == NOTE and entry.created_at is not None
    assert entry.details == {"identity_checked_in_person": True, "document_matched": True}
    assert DOCUMENT not in str(entry.details) + entry.reason
    email = OutgoingEmail.objects.get(template=personal_reset.NOTICE_TEMPLATE)
    assert email.to_address == "rita@example.org"
    assert "http" not in email.body_text  # cap enllaç ni codi
    notice = AuditEntry.objects.filter(action="auth.reset_notice").get()
    assert notice.details["result"] == "queued"


def test_the_holder_can_log_in_with_the_password_and_set_a_new_factor(soci, secretary, client):
    from apps.accounts import totp

    member, account = soci
    post(admin_client(secretary), member, secretary)
    response = client.post(
        reverse("accounts:login"), {"login": account.login, "password": PASSWORD}
    )
    assert response.status_code == 302
    assert response["Location"] != reverse("accounts:login_totp")
    device = totp.start_enrolment(account)
    assert device.confirmed_at is None  # el titular el pot tornar a donar d'alta
    assert not RecoveryCode.objects.filter(account=account).exists()  # cap codi personal (081)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"document": "87654321X"}, "El document no coincideix"),
        ({"identity_checked": ""}, "This field is required"),
        ({"note": "  "}, "This field is required"),
        ({"code": "000000"}, "Codi incorrecte"),
    ],
)
def test_without_every_check_nothing_changes(soci, secretary, overrides, message):
    member, account = soci
    response = post(admin_client(secretary), member, secretary, **overrides)
    assert response.status_code == 200
    assert TotpDevice.objects.filter(account=account).exists()
    assert not AuditEntry.objects.filter(action=personal_reset.PERSONAL_TOTP_RESET).exists()
    assert not OutgoingEmail.objects.filter(template=personal_reset.NOTICE_TEMPLATE).exists()


def test_service_rejects_without_m2_own_account_and_without_document(soci, make_admin):  # noqa: F811
    member, account = soci
    kwargs = {"document": DOCUMENT, "identity_checked": True, "note": NOTE}
    with pytest.raises(Http404):
        personal_reset.reset_personal_totp(account, by=make_admin("treasurer"), **kwargs)
    own = make_admin("secretary", person=member.person, username="rita.admin")
    with pytest.raises(ValidationError):
        personal_reset.reset_personal_totp(account, by=own, **kwargs)
    Person.objects.filter(pk=member.person_id).update(id_document_type="", id_document_number="")
    with pytest.raises(ValidationError):
        personal_reset.reset_personal_totp(account, by=make_admin("secretary"), **kwargs)
    assert TotpDevice.objects.filter(account=account).exists()


def test_admin_accounts_are_not_reset_this_way(make_admin, secretary):  # noqa: F811
    other = make_admin("treasurer")
    with pytest.raises(ValidationError):
        personal_reset.reset_personal_totp(
            other, by=secretary, document=DOCUMENT, identity_checked=True, note=NOTE
        )
    assert TotpDevice.objects.filter(account=other).exists()


def test_no_email_path_removes_the_factor(soci, client):
    """Cap camí per correu: la recuperació de la contrasenya amb l'enllaç no treu el doble factor
    i l'entrada continua demanant el codi."""
    member, account = soci
    token = tokens.make_token(account, tokens.RESET_PASSWORD)
    # La contrasenya de proves és el valor únic de CLAUDE.md (també com a «nova»).
    result = email_links.reset_password(
        token, {"new_password1": PASSWORD, "new_password2": PASSWORD}
    )
    assert result.done is True  # la recuperació s'ha fet de debò
    assert TotpDevice.objects.filter(account=account, confirmed_at__isnull=False).exists()
