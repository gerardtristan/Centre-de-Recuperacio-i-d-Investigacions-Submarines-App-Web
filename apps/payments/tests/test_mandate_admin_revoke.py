"""Revocar un mandat des de l'administració, a petició escrita del soci (T-M05a-10; A6; P-M05a-C;
P-133). Cel·la de cada rol, motiu obligatori, mandat propi i correu al soci. Només dades
inventades."""

import pytest
from django.urls import reverse

from apps.core.models import AuditEntry, OutgoingEmail, Person, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.payments.models import FeePaymentPreference, SepaMandate
from apps.payments.tests import test_mandates
from apps.payments.tests.test_preferences import prefer
from apps.treasury.tests.test_views import client_for

pytestmark = pytest.mark.django_db
R = Role.Code
MANAGEMENT_ROLES = [code for code in R.values if code not in ("member", "visitor", "guest")]
WITH_A6 = {R.TREASURER, R.ADMINISTRATOR}
LIST = reverse("administration:payments_mandates")
REASON = "Correu del soci del 15/11/2026 demanant la baixa de la domiciliació."
# Les mateixes fixtures que les proves del mandat.
member, account, text, sign = (
    test_mandates.member,
    test_mandates.account,
    test_mandates.text,
    test_mandates.sign,
)


@pytest.fixture
def mandate(sign, member, account):
    mandate = sign()
    prefer(member, account, "direct_debit", mandate=mandate)
    return mandate


def url(mandate):
    return reverse("administration:payments_mandate_revoke", args=[mandate.pk])


def reloaded(mandate):
    mandate.refresh_from_db()
    return mandate


@pytest.mark.parametrize("role", MANAGEMENT_ROLES)
def test_a6_cell_of_each_role(make_admin, mandate, role):  # noqa: F811
    response = client_for(make_admin(role)).get(url(mandate))
    assert response.status_code == (200 if role in WITH_A6 else 404)


def test_the_treasurer_revokes_with_a_reason_and_the_member_is_told(make_admin, mandate):  # noqa: F811
    Person.objects.filter(pk=mandate.member.person_id).update(contact_email="anna@example.org")
    treasurer = make_admin(R.TREASURER)
    client = client_for(treasurer)
    page = client.get(LIST).content.decode()
    assert url(mandate) in page

    assert "Cal el motiu" in client.post(url(mandate), {"reason": ""}).content.decode()
    assert reloaded(mandate).status == SepaMandate.Status.ACTIVE

    response = client.post(url(mandate), {"reason": REASON})
    assert response.status_code == 302 and response.url == LIST
    mandate = reloaded(mandate)
    assert mandate.status == SepaMandate.Status.REVOKED
    assert (mandate.revoked_reason, mandate.revoked_by) == (REASON, treasurer)
    assert FeePaymentPreference.objects.get().method == "pay_each_time"
    entry = AuditEntry.objects.get(action="payments.mandate.revoked")
    assert entry.reason == REASON and entry.actor_account == treasurer
    email = OutgoingEmail.objects.get(template="mandat-revocat")
    assert email.to_address == "anna@example.org" and mandate.reference in email.subject
    assert test_mandates.IBAN[4:] not in email.body_text
    # Un mandat ja revocat no es pot tornar a obrir.
    assert client.get(url(mandate)).status_code == 404


def test_an_admin_cannot_revoke_their_own_mandate(make_admin, mandate):  # noqa: F811
    own = client_for(make_admin(R.TREASURER, person=mandate.member.person))
    assert url(mandate) not in own.get(LIST).content.decode()
    page = own.post(url(mandate), {"reason": REASON}).content.decode()
    assert "És el teu mandat" in page
    assert reloaded(mandate).status == SepaMandate.Status.ACTIVE


def test_only_post_with_a_session_and_never_the_iban(make_admin, mandate):  # noqa: F811
    page = client_for(make_admin(R.TREASURER)).get(url(mandate)).content.decode()
    assert mandate.reference in page and "ES … 0001" in page
    assert test_mandates.IBAN[4:] not in page
