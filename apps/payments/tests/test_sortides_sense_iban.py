"""Cap sortida de la plataforma porta l'IBAN (T-M05a-17; CA-M05a-06 i 07; decisió 044).

Un sol recorregut: el soci signa un mandat amb un IBAN inventat de dígits reconeixibles, en revoca
un, en signa un altre que caduca, i el club en fa la campanya. Després es miren totes les sortides
que existeixen avui: pantalles del soci i de l'administració, correus (assumpte, text i HTML),
registre d'activitat, registres de l'aplicació, informe d'error de Django, exportació RGPD, dades
bloquejades i CSV del llistat de socis. Hi pot sortir l'IBAN emmascarat (país i quatre darrers),
mai cap xifra més. Només dades inventades: el banc «0000» no existeix."""

import json
import logging
import sys
from datetime import timedelta

import pytest
from django.core.signals import got_request_exception
from django.urls import reverse
from django.utils import timezone
from django.views.debug import ExceptionReporter

from apps.accounts.models import Account
from apps.accounts.security import AREA_PERSONAL
from apps.core.models import AuditEntry, LegalText, LockedIdentity, OutgoingEmail, Person, Role
from apps.core.privacy import anonymise_person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.privacy import export_personal_data
from apps.members.tests.test_cards import add_fee, make_member
from apps.payments import campaigns, crypto, expiry
from apps.payments.models import SepaMandate
from apps.treasury.tests.test_views import client_for
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

IBAN = "ES1200000000007395184260"  # mòdul 97 vàlid; compte inventat
TYPED = "es12 0000 0000 0073 9518 4260"  # com l'escriuria el soci
BAD = "ES1300000000007395184260"  # un dígit de control canviat
# L'IBAN sencer, agrupat, sense el país i les xifres del compte més enllà dels quatre darrers.
NEEDLES = (IBAN, "ES12 0000 0000 0073 9518 4260", IBAN[4:], "739518", "7395 18", "0073 9518")


def assert_clean(text, where):
    text = str(text)
    for needle in NEEDLES:
        assert needle.lower() not in text.lower(), f"L'IBAN surt a {where} («{needle}»)"


@pytest.fixture(autouse=True)
def platform(settings):
    settings.MANDATE_SIGNING_ENABLED = True
    settings.SEPA_CREDITOR_IDENTIFIER = "ES00ZZZ00000000"
    settings.PUBLIC_SITE_URL = "https://cris1954.cat"
    LegalText.objects.create(kind="sepa_mandate", version=1, content="Esborrany de prova.")
    LegalText.objects.create(kind=campaigns.INVITATION_TEXT, version=1, content="Invitació.")


@pytest.fixture
def member():
    member = make_member()
    member.person.contact_email = "anna.prova@example.org"
    member.person.save()
    return member


@pytest.fixture
def browser(login_as, member):
    account = Account.objects.create_personal(member.person, "anna.prova@example.org", PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    return login_as(account, AREA_PERSONAL)


@pytest.fixture
def admin_account(make_admin):  # noqa: F811
    return make_admin(Role.Code.ADMINISTRATOR)


@pytest.fixture
def admin(admin_account):
    return client_for(admin_account)


def sign(browser, iban=TYPED):
    return browser.post(
        reverse("payments:mandate"), {"holder_name": "Anna Prova", "iban": iban, "accept": "on"}
    )


def test_ca_m05a_06_cap_sortida_porta_l_iban(browser, admin, admin_account, member, caplog):
    caplog.set_level(logging.DEBUG)
    outputs = []  # (on, text)

    # Soci: signa, mira les seves pàgines, revoca i en signa un altre.
    outputs.append(("la signatura", sign(browser).content.decode()))
    assert SepaMandate.objects.filter(status="active").count() == 1
    for name in ("payments:mandate", "payments:mandate_revoke", "payments:fee_method"):
        page = browser.get(reverse(name))
        assert page.status_code == 200
        assert "4260" in page.content.decode() or name == "payments:fee_method"
        outputs.append((name, page.content.decode()))
    browser.post(reverse("payments:fee_method"), {"method": "direct_debit"})
    revoked = browser.post(reverse("payments:mandate_revoke"), follow=True)
    outputs.append(("la revocació", revoked.content.decode()))
    outputs.append(("la segona signatura", sign(browser, IBAN).content.decode()))

    # Administració: mètodes i mandats, campanya, llistat en CSV.
    campaign = campaigns.open_campaign("Prova", by=admin_account)
    jordi = make_member("Jordi", number=311, document="00000001R")
    Person.objects.filter(pk=jordi.person_id).update(contact_email="jordi.prova@example.org")
    campaigns.send_invitations(campaign, by=admin_account)
    for name in ("administration:payments_mandates", "administration:payments_campaign"):
        page = admin.get(reverse(name))
        assert page.status_code == 200
        outputs.append((name, page.content.decode()))
    csv = admin.post(reverse("administration:members_export"), {"format": "csv"})
    assert csv.status_code == 200
    outputs.append(("el CSV del llistat", csv.content.decode("utf-8-sig")))

    # Caducitat del mandat vigent (correu d'avís).
    later = timezone.localdate() + timedelta(days=4 * 366)
    assert expiry.expire_mandates(today=later) == 1

    # Exportació RGPD i dades bloquejades (amb un càrrec, com un soci real).
    outputs.append(
        ("l'exportació RGPD", json.dumps(export_personal_data(member.person), default=str))
    )
    add_fee(member)
    anonymise_person(member.person, by=admin_account)
    item = LockedIdentity.objects.get(person=member.person)
    outputs.append(
        ("les dades bloquejades", admin.get(reverse("administration:locked_data")).content.decode())
    )
    detail = reverse("administration:locked_data_detail", args=[item.pk])
    consulted = admin.post(detail, {"reason": "Comprovació de la prova T-M05a-17."})
    assert consulted.status_code == 200
    outputs.append(("la consulta de dades bloquejades", consulted.content.decode()))

    # Correus: tots els que s'han posat a la cua (G3, caducitat, campanya i, si n'hi ha,
    # la revocació).
    emails = list(OutgoingEmail.objects.all())
    assert {"mandat-signat", "mandat-caducat", campaigns.INVITATION_TEMPLATE} <= {
        e.template for e in emails
    }
    for email in emails:
        outputs.append(
            (f"el correu {email.template}", email.subject + email.body_text + email.body_html)
        )

    # Registre d'activitat i registres de l'aplicació.
    for entry in AuditEntry.objects.all():
        values = json.dumps(
            [entry.old_value, entry.new_value, entry.reason, entry.details], default=str
        )
        outputs.append((f"el registre d'activitat ({entry.action})", values))
    outputs.append(("els registres de l'aplicació", caplog.text))

    for where, text in outputs:
        assert_clean(text, where)


def test_un_iban_rebutjat_no_torna_a_la_resposta_ni_als_registres(browser, caplog):
    caplog.set_level(logging.DEBUG)
    response = sign(browser, BAD)

    assert response.status_code == 200
    assert not SepaMandate.objects.exists()
    assert_clean(response.content.decode(), "la resposta d'un IBAN rebutjat")
    assert_clean(caplog.text, "els registres d'un IBAN rebutjat")
    assert_clean(json.dumps([e.details for e in AuditEntry.objects.all()]), "el registre")


def test_l_informe_d_error_de_django_no_porta_l_iban(login_as, member, monkeypatch, caplog):
    """Un error en desar el mandat (aquí, la clau) genera l'informe d'error que rebria
    l'administrador: ni les dades del POST ni les variables locals hi porten l'IBAN."""
    account = Account.objects.create_personal(member.person, "anna.prova@example.org", PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    browser = login_as(account, AREA_PERSONAL)
    browser.raise_request_exception = False

    def broken(plaintext):
        raise RuntimeError("Clau no disponible")

    monkeypatch.setattr(crypto, "encrypt", broken)
    reports = []

    def report(sender, request, **kwargs):
        reporter = ExceptionReporter(request, *sys.exc_info())
        reports.append(reporter.get_traceback_text() + reporter.get_traceback_html())

    got_request_exception.connect(report)
    try:
        response = sign(browser)
    finally:
        got_request_exception.disconnect(report)

    assert response.status_code == 500
    assert reports and "Clau no disponible" in reports[0]
    assert_clean(reports[0], "l'informe d'error")
    assert_clean(caplog.text, "els registres de l'error")
