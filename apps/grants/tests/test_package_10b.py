"""T-M09A-10b: enviar el paquet, paquet congelat, versions amb requeriment i avisos (RN-M09A-11,
18 i 21; CA-M09A-16, 20 i 24). Només dades i fitxers inventats."""

from datetime import date

import pytest

from apps.core import mail
from apps.core.models import OutgoingEmail
from apps.expenses import documents
from apps.expenses import services as expenses
from apps.grants import justification as j
from apps.grants import package as p
from apps.grants.models import GrantApplication, GrantExpenseLink
from apps.grants.tests.test_package_10a import PROOF, granted, linked  # noqa: F401 (fixture)
from apps.grants.tests.test_requirements import record
from apps.grants.tests.test_resolution import submitted  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db
SENT = date(2027, 9, 1)


@pytest.fixture
def justified(granted, treasurer):  # noqa: F811
    treasurer.notification_email = "tresoreria@example.org"
    treasurer.save()
    first = linked(granted, treasurer, 50000, "F-1")
    second = linked(granted, treasurer, 24000, "F-2")
    package = p.build_package(granted, treasurer)
    p.submit_package_version(granted, package, sent_on=SENT, by=treasurer)
    granted.refresh_from_db()
    return granted, package, first, second


SUBJECTS = {
    "excluded": "despeses fora del paquet",
    "annulled": "s'ha anul·lat una despesa",
    "illegible": "és il·legible",
}


def notices(kind):
    return OutgoingEmail.objects.filter(
        template=p.NOTICE_TEMPLATE, subject__contains=SUBJECTS[kind]
    )


def test_version_1_justifies_and_freezes_the_package(justified):
    application, package, first, second = justified
    assert (application.status, application.justified_on) == ("justified", SENT)
    assert application.submitted_package == package
    submission = application.submissions.get()
    assert (submission.version, submission.requirement) == (1, None)


def test_ca_m09a_16_annulling_an_included_expense_warns_and_changes_nothing(justified, treasurer):
    application, package, first, second = justified
    expenses.annul(second, reason="Duplicada", by=treasurer)
    package.refresh_from_db()
    assert [i["expense"] for i in package.items] == [first.pk, second.pk]
    assert notices("annulled").get().to_address == "tresoreria@example.org"
    with pytest.raises(j.AlreadyJustified):
        p.build_package(application, treasurer)
    with pytest.raises(j.AlreadyJustified):
        linked(application, treasurer, 1000, "F-8")


def test_ca_m09a_20_a_new_version_with_an_open_requirement(justified, treasurer):
    application, package, first, second = justified
    requirement = record(application, treasurer)
    link = GrantExpenseLink.objects.get(expense=second, removed_at__isnull=True)
    j.unlink_expense(link, by=treasurer, requirement=requirement)
    third = linked(application, treasurer, 10000, "F-3", requirement=requirement)
    new = p.build_package(application, treasurer, requirement=requirement)
    assert [i["expense"] for i in new.items] == [first.pk, third.pk]
    assert new.totals["included_cents"] == 60000
    v2 = p.submit_package_version(application, new, sent_on=date(2027, 10, 10), by=treasurer,
                                  requirement=requirement)  # fmt: skip
    requirement.refresh_from_db()
    application.refresh_from_db()
    assert (v2.version, v2.requirement, requirement.answered_on) == (
        2, requirement, date(2027, 10, 10),
    )  # fmt: skip
    assert application.status == "justified" and application.submitted_package == package
    package.refresh_from_db()
    assert [i["expense"] for i in package.items] == [first.pk, second.pk]  # la versió 1, igual


def test_ca_m09a_24_an_illegible_document_of_a_sent_version_warns(justified, treasurer):
    application, package, first, second = justified
    documents.mark_illegible(second, PROOF, reason="No es llegeix", by=treasurer)
    notice = notices("illegible").get()
    assert f"despesa {second.pk}, que és a la versió 1" in notice.body_text
    package.refresh_from_db()
    assert len(package.items) == 2


def test_an_expense_outside_any_sent_version_does_not_warn(granted, treasurer):  # noqa: F811
    loose = linked(granted, treasurer, 1000, "F-9")
    expenses.annul(loose, reason="Duplicada", by=treasurer)
    assert not notices("annulled").exists()


def test_rn_m09a_11_excluded_expenses_warn_the_treasurer(granted, treasurer):  # noqa: F811
    treasurer.notification_email = "tresoreria@example.org"
    treasurer.save()
    linked(granted, treasurer, 6500, "F-3", docs=(PROOF,))
    p.build_package(granted, treasurer)
    assert "1 despesa n'ha quedat fora" in notices("excluded").get().body_text


def test_a_package_is_sent_once_and_a_new_version_needs_the_requirement(justified, treasurer):
    application, package, first, second = justified
    with pytest.raises(p.PackageAlreadySent):
        p.submit_package_version(application, package, sent_on=SENT, by=treasurer)
    requirement = record(application, treasurer)
    new = p.build_package(application, treasurer, requirement=requirement)
    with pytest.raises(p.RequirementNotOpen):
        p.submit_package_version(application, new, sent_on=SENT, by=treasurer)


def test_only_a_granted_application_is_justified(granted, treasurer):  # noqa: F811
    package = p.build_package(granted, treasurer)
    GrantApplication.objects.filter(pk=granted.pk).update(status="submitted")
    with pytest.raises(p.GrantError):
        p.submit_package_version(granted, package, sent_on=SENT, by=treasurer)


@pytest.mark.parametrize(
    ("kind", "extra", "text"),
    [
        ("excluded", {"count": 2}, "2 despeses"),
        ("annulled", {"version": 1, "expense_id": 9}, "despesa 9"),
        ("illegible", {"version": 2, "expense_id": 9, "document": "Factura"}, "«Factura»"),
    ],
)
def test_the_notice_template(kind, extra, text):
    context = {"kind": kind, "application_id": 7, "call": "Medi marí", "body": "Diputació", **extra}
    email = mail.queue_email(p.NOTICE_TEMPLATE, to="tresoreria@example.org", context=context)
    assert text in email.body_text and "sol·licitud 7" in email.body_text and email.subject
