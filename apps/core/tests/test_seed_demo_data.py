"""Ordre de dades inventades: es nega fora de desenvolupament i proves, crea els casos de la
revisió (T-M01-27) i els comptes de prova amb el TOTP de prova fix (074, punt 21)."""

import re
from io import StringIO

import pyotp
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import override_settings
from django.utils import timezone

from apps.accounts import totp
from apps.accounts.models import Account, TotpDevice
from apps.accounts.totp import DEMO_TOTP_SECRET
from apps.activities import guests
from apps.core import audit
from apps.core.management.commands.seed_demo_data import (
    ADMIN_LOGIN,
    PASSWORD,
    ROLE_ACCOUNTS,
    demo_people,
)
from apps.core.models import AuditEntry, Charge, Consent, ImportBatch, LegalText, Person
from apps.core.roles import operational_admins
from apps.members import services
from apps.members.imports import cluber
from apps.members.join import OPTIONAL_TEXT_CONTENT
from apps.members.models import AnnualFee, LicenceRecord, Member, MemberCard, MemberRequest

pytestmark = pytest.mark.django_db
DEV = override_settings(SETTINGS_MODULE="config.settings.dev", DEBUG=True)
BASE_DOCUMENT = r"^PROVA\d{4}$"  # les persones de la llavor (no els socis de la revisió)


@pytest.fixture
def cluber_path(tmp_path):
    return tmp_path / "cluber.csv"


def run(*args, cluber_path=None):
    out = StringIO()
    if cluber_path is not None:
        args = (*args, "--cluber-file", str(cluber_path))
    call_command("seed_demo_data", *args, stdout=out)
    return out.getvalue()


def nothing_created():
    return not (Person.objects.exists() or Account.objects.exists() or TotpDevice.objects.exists())


@pytest.mark.parametrize(
    ("module", "debug"),
    [
        ("config.settings.prod", True),
        ("config.settings.prod", False),
        ("config.settings.dev", False),
        (None, True),
    ],
)
def test_t_m01_27_refuses_outside_development(module, debug, cluber_path):
    """Fora de desenvolupament amb DEBUG: es nega i no crea res, cap compte amb TOTP (074)."""
    with override_settings(SETTINGS_MODULE=module, DEBUG=debug), pytest.raises(CommandError):
        run(cluber_path=cluber_path)
    assert nothing_created()
    assert not cluber_path.exists()


@pytest.mark.parametrize("host", ["db.example.org", "10.0.0.5"])
def test_refuses_a_database_that_is_not_local(monkeypatch, host):
    monkeypatch.setitem(connection.settings_dict, "HOST", host)
    with DEV, pytest.raises(CommandError):
        run()
    assert nothing_created()


def test_refuses_a_database_with_data(make_person):
    make_person()
    with DEV, pytest.raises(CommandError):
        run()
    assert Person.objects.count() == 1


def test_same_seed_same_people():
    assert demo_people(1954) == demo_people(1954)
    assert demo_people(1954) != demo_people(7)


@DEV
def test_creates_the_people_of_the_seed(cluber_path):
    run("--seed", "7", cluber_path=cluber_path)
    created = Person.objects.filter(id_document_number__regex=BASE_DOCUMENT)
    expected = sorted(demo_people(7), key=lambda p: p["id_document_number"])
    assert [
        (p.first_name, p.last_name, p.contact_email) for p in created.order_by("id_document_number")
    ] == [(p["first_name"], p["last_name"], p["contact_email"]) for p in expected]


@DEV
def test_t_m01_27_second_run_is_refused_and_duplicates_nothing(cluber_path):
    run(cluber_path=cluber_path)
    counts = (Person.objects.count(), Account.objects.count(), Member.objects.count())
    with pytest.raises(CommandError):
        run(cluber_path=cluber_path)
    assert (Person.objects.count(), Account.objects.count(), Member.objects.count()) == counts


@DEV
def test_t_m01_27_only_invented_data(cluber_path):
    run(cluber_path=cluber_path)
    for person in Person.objects.all():
        assert person.contact_email == "" or person.contact_email.endswith("@example.org")
        assert person.id_document_number == "" or person.id_document_number.startswith("PROVA")
        assert person.phone == "" or person.phone.startswith("+34600000")
        assert person.address == ""
    for request in MemberRequest.objects.exclude(guardian_email=""):
        assert request.guardian_email.endswith("@example.org")
        assert request.guardian_id_document_number.startswith("PROVAT")
    # Cap IBAN al fitxer de Cluber: la columna hi és, però buida.
    assert "IBAN" not in cluber_path.read_bytes().decode("cp1252").split("\r\n", 1)[1]


@DEV
def test_t_m01_27_role_accounts_are_operational_with_the_test_totp(cluber_path):
    """Cada compte d'administració de prova valida un codi del secret de prova (074, punt 21),
    només amb DEBUG (`DEV`; sense, el rebutja: 075, CA-M01-86 a `test_retocs_075.py`)."""
    output = run(cluber_path=cluber_path)
    for login, _name, role in ROLE_ACCOUNTS:
        account = Account.objects.get(login=login)
        assert account.kind == Account.Kind.ADMIN and account.status == Account.Status.ACTIVE
        assert account.check_password(PASSWORD)
        assert account.role_assignments.filter(role__code=role, removed_at=None).exists()
        assert totp.verify_code(account.totp_device, pyotp.TOTP(DEMO_TOTP_SECRET).now())
        assert login in output
    admin = Account.objects.get(login=ADMIN_LOGIN)
    assert list(operational_admins()) == [admin]
    entry = AuditEntry.objects.get(action=audit.Action.ROLE_ASSIGNED, target_id=str(admin.pk))
    assert (entry.actor_kind, entry.actor_origin) == ("system", "seed_demo_data")
    # Com entrar-hi: la contrasenya de proves i el secret, cap QR.
    assert PASSWORD in output and DEMO_TOTP_SECRET in output and "<svg" not in output


@DEV
def test_t_m01_27_members_of_every_review_case(cluber_path):
    run(cluber_path=cluber_path)
    today = timezone.localdate()
    S, K, R = Member.Status, MemberRequest.Kind, MemberRequest.Status

    def member(email):
        return Member.objects.get(person__contact_email=email)

    assert member("simpatitzant.pagat@example.org").type.code == "supporter"
    for email in ("simpatitzant.pagat@example.org", "ple.dret.pagat@example.org"):
        assert member(email).status == S.ACTIVE
        # La primera, pagada; Pau en té una altra de l'any vinent a la remesa (T-M04-18).
        assert member(email).fees.order_by("pk").first().charge.status == Charge.Status.PAID
    exempt = member("exempt.edat@example.org")
    assert exempt.status == S.ACTIVE and not exempt.fees.exists()
    imported = Member.objects.filter(person__origin=Person.Origin.CLUBER_IMPORT)
    assert imported.count() == 2 and all(m.status == S.ACTIVE for m in imported)
    cluber_batches = ImportBatch.objects.filter(kind=ImportBatch.Kind.CLUBER)
    assert cluber_batches.filter(status=ImportBatch.Status.CONFIRMED).count() == 1
    unpaid = member("impagat@example.org")
    assert unpaid.status == S.UNPAID
    assert unpaid.fees.get().charge.status == Charge.Status.RETURNED

    change = member("canvi.pendent@example.org").requests.get(kind=K.CHANGE_TYPE)
    assert change.status == R.PENDING and change.supplement_fee is None
    pending = member("suplement.pendent@example.org").requests.get(kind=K.CHANGE_TYPE)
    assert pending.status == R.APPROVED and pending.effective_on is None
    assert pending.supplement_fee.charge.status == Charge.Status.PENDING
    assert pending.supplement_fee.due_on > today
    overdue = member("suplement.vencut@example.org").requests.get(kind=K.CHANGE_TYPE)
    assert overdue.supplement_fee.due_on < today
    assert overdue.supplement_fee.charge.status == Charge.Status.PENDING

    assert member("baixa.pendent@example.org").requests.get(kind=K.LEAVE).status == R.PENDING
    scheduled = member("baixa.programada@example.org")
    leave = scheduled.requests.get(kind=K.LEAVE)
    assert scheduled.status == S.ACTIVE and leave.status == R.APPROVED
    assert leave.effective_on > today and leave.applied_at is None
    left = member("de.baixa@example.org")
    assert left.status == S.LEFT and left.left_on == today
    assert left.fees.get(period=today.year + 1).charge.status == Charge.Status.CANCELLED

    young = Member.objects.get(person__first_name="Mia")
    young_join = MemberRequest.objects.get(person=young.person, kind=K.JOIN)
    assert young.status == S.ACTIVE and young_join.guardian_email and young_join.guardian_phone
    teen = Member.objects.get(person__first_name="Pol")
    assert teen.person.contact_email == "" and teen.status == S.ACTIVE
    pending_joins = MemberRequest.objects.filter(kind=K.JOIN, status=R.PENDING)
    assert sorted(bool(j.guardian_email) for j in pending_joins) == [False, True]


@DEV
def test_t_m01_27_fees_cards_licences_texts_and_consents(cluber_path):
    output = run(cluber_path=cluber_path)
    assert {f.charge.status for f in AnnualFee.objects.select_related("charge")} == {
        Charge.Status.PENDING,
        Charge.Status.PAID,
        Charge.Status.RETURNED,
        Charge.Status.CANCELLED,
    }
    assert MemberCard.objects.filter(revoked_at=None).exists()
    assert MemberCard.objects.exclude(revoked_at=None).exists()
    tokens = re.findall(r"/carnet/verificar/([^/\s]+)/", output)
    assert [services.verify_card(t)["valid"] for t in tokens] == [True, False]

    records = LicenceRecord.objects.all()
    assert records.filter(expires_on__isnull=False, expiry_declared=False).exists()
    assert records.filter(expires_on=None).exists()
    declared = records.get(expiry_declared=True)
    assert services.licence_record(declared.member.person).expires_on is None

    for kind, content in OPTIONAL_TEXT_CONTENT.items():
        assert LegalText.objects.get(kind=kind).content == content
    # Decisió 085 (G-4): textos definitius, sense marques pendents.
    assert "A validar" not in LegalText.objects.get(kind="images").content
    assert "xarxes socials" in LegalText.objects.get(kind="images").content
    # T-M02-34 (P-458): a local, la proposta de «Soc major d'edat» publicada perquè el formulari
    # de convidats del 02 funcioni; a producció no hi ha cap versió fins que la junta la validi.
    assert LegalText.objects.get(kind=guests.ADULT).content == guests.ADULT_PROPOSAL
    given = Consent.objects.filter(legal_text__kind__in=["newsletter", "images"])
    assert given.filter(person__member__isnull=False).exists()
    assert given.filter(given_by=Consent.GivenBy.GUARDIAN).exists()  # imatges d'un menor de 14

    personal = Account.objects.filter(kind=Account.Kind.PERSONAL)
    assert personal.count() >= 5
    assert all(a.status == Account.Status.ACTIVE and a.check_password(PASSWORD) for a in personal)


@DEV
def test_t_m01_27_cluber_file_is_read_by_the_preview(cluber_path):
    """Sense el lot confirmat, la previsualització llegeix el fitxer sense errors de format."""
    output = run("--without-cluber-batch", cluber_path=cluber_path)
    assert str(cluber_path) in output
    assert not ImportBatch.objects.filter(kind=ImportBatch.Kind.CLUBER).exists()
    assert not Member.objects.filter(person__origin=Person.Origin.CLUBER_IMPORT).exists()
    result = cluber.preview(cluber_path.read_bytes())
    assert result.rejected is None
    assert result.encoding == "windows-1252"
    assert result.counts["rows"] == 40 and result.counts["with_errors"] == 0
    assert result.counts["new"] == 40  # cap número ni document d'un soci creat


@DEV
def test_t_m01_27_with_the_batch_the_preview_says_it_is_already_imported(cluber_path):
    run(cluber_path=cluber_path)
    assert cluber.preview(cluber_path.read_bytes()).rejected == "cluber_already_imported"


@DEV
def test_covers_the_charge_and_consent_states_shown_in_captures(cluber_path):
    run(cluber_path=cluber_path)
    assert set(Charge.objects.values_list("status", flat=True)) == {
        Charge.Status.PENDING,
        Charge.Status.PAID,
        Charge.Status.RETURNED,
        Charge.Status.CANCELLED,
    }
    assert set(Consent.objects.values_list("action", flat=True)) == {
        Consent.Action.GRANTED,
        Consent.Action.WITHDRAWN,
    }
    assert {Consent.Channel.WEB, Consent.Channel.IN_PERSON} <= set(
        Consent.objects.values_list("channel", flat=True)
    )


@DEV
def test_t_m02_25_the_seed_loads_the_activities_with_the_courses_manager(cluber_path):
    """«Es carreguen amb una ordre»: la mateixa de la resta de dades inventades, amb un compte de
    prova del responsable de cursos i sortides."""
    from apps.activities.models import Activity, Enrolment

    output = run(cluber_path=cluber_path)
    manager = Account.objects.get(login="cursos-demo")
    assert manager.role_assignments.filter(role__code="courses_manager").exists()
    assert Activity.objects.filter(responsible=manager.person).count() == 5
    assert Enrolment.objects.count() == 4
    assert "Mòdul 02: 3 fitxes del catàleg, 5 activitats i 4 inscripcions." in output


@DEV
def test_t_m02_30_the_demo_instructor_is_a_member_with_a_technical_licence(cluber_path):
    """RN-M02-26: l'instructor de prova pot fer classe en mode «bloqueig», i les sessions de prova
    el tenen com a instructor."""
    from apps.activities import sessions
    from apps.activities.models import Session

    run(cluber_path=cluber_path)
    teacher = Account.objects.get(login="instructor-demo").person
    assert services.is_member(teacher)
    assert sessions.instructor_problems(teacher, timezone.localdate()) == []
    assert Session.objects.filter(instructors=teacher).exists()
