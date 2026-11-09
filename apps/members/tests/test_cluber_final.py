"""Importació de Cluber, fase final (T-M01-25; CA-M01-22 i CA-M01-23; decisió 071).

Bloqueig per configuració, recorregut de confirmació del servei (exclusions, files importables,
transacció), creació de persones, socis, consentiments, lot i línies, i que cap IBAN arriba
enlloc. Només dades inventades.

Avui cap fila de Cluber no és importable: totes tenen pendent el document o el seu tipus
(P-62, punt 5). Per provar l'escriptura, `future_document_rule` treu **només a les proves** el
pendent «id_document» de les files sense document; el codi de producció no ho simula.
"""

import datetime
import logging

import pytest
from django.apps import apps
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.core import consents
from apps.core.models import (
    IMPORT_LINE_CODES,
    AuditEntry,
    Charge,
    Consent,
    ImportBatch,
    ImportLine,
    LegalText,
    Person,
)
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.imports import cluber, final
from apps.members.models import (
    AnnualFee,
    Member,
    MembershipNumberCounter,
    MembershipType,
    MemberStatusChange,
)
from apps.members.tests.test_cluber_format import FALSE_IBAN, real_headers, sample_file
from apps.members.tests.test_cluber_preview import build, dni, record

SHA = "a" * 64  # empremta inventada: quina es desa és la P-65, punt 1
allowed = pytest.mark.usefixtures("allow")

WRITTEN = (Person, Member, MemberStatusChange, Consent, LegalText, ImportBatch, ImportLine)


def snapshot():
    return {model.__name__: model.objects.count() for model in (*WRITTEN, AuditEntry, Charge)}


def importable_record(n, values=None):
    """Fila sense document (l'única forma que el servei podria importar) i amb el tipus pel nom."""
    return record(
        n,
        {
            "Document d'Identitat": "",
            "Quota": "Quota de soci simpatitzant 35€.",
            "idInterno": f"cl-{n:05d}",
            cluber.IMAGE_CONSENT: "Sí",
            **(values or {}),
        },
    )


@pytest.fixture
def allow(settings):
    settings.CLUBER_FINAL_IMPORT_ALLOWED = True


@pytest.fixture
def admin(make_admin):  # noqa: F811
    return make_admin("administrator")


@pytest.fixture
def future_document_rule(monkeypatch):
    """Simula NOMÉS a les proves una decisió futura de la P-62 (punt 5): una fila sense document
    deixa de tenir-lo pendent. El tipus pendent d'una fila amb document no es toca."""
    real = cluber.preview

    def preview(data, **kwargs):
        result = real(data, **kwargs)
        for row in result.rows:
            if "id_document" in row.pending:
                row.pending.remove("id_document")
        return result

    monkeypatch.setattr(cluber, "preview", preview)


class TestBlockedByConfiguration:
    """CA-M01-23: amb la configuració per defecte, el servidor ho rebutja i no escriu res."""

    def test_the_option_is_off_by_default(self):
        assert getattr(settings, "CLUBER_FINAL_IMPORT_ALLOWED", False) is not True
        assert final.is_allowed() is False

    @pytest.mark.parametrize("value", [False, "True", "1", 1, None])
    def test_only_the_boolean_true_unlocks_it(self, value):
        with override_settings(CLUBER_FINAL_IMPORT_ALLOWED=value):
            assert final.is_allowed() is False
        with override_settings(CLUBER_FINAL_IMPORT_ALLOWED=True):
            assert final.is_allowed() is True

    def test_blocked_before_reading_the_file_or_querying(self, admin, monkeypatch):
        def must_not_run(*args, **kwargs):
            raise AssertionError("preview() no s'ha de cridar")

        monkeypatch.setattr(cluber, "preview", must_not_run)
        before = snapshot()
        with CaptureQueriesContext(connection) as queries, pytest.raises(final.FinalImportBlocked):
            final.confirm(sample_file(), by=admin, file_sha256=SHA)
        assert len(queries) == 0
        assert snapshot() == before

    def test_blocked_even_with_an_importable_file(self, admin, future_document_rule):
        before = snapshot()
        with pytest.raises(final.FinalImportBlocked):
            final.confirm(build([importable_record(1)]), by=admin, file_sha256=SHA)
        assert snapshot() == before
        assert MembershipNumberCounter.objects.get().last_number == 0

    def test_the_rejection_is_a_permission_denied(self):
        # Un punt d'entrada que no el capturi respon 403, no 500.
        assert issubclass(final.FinalImportBlocked, PermissionDenied)


@allowed
class TestConfirmationPath:
    def test_needs_p18(self, make_admin, future_document_rule):  # noqa: F811
        without_p18 = make_admin()
        before = snapshot()
        with pytest.raises(PermissionDenied):
            final.confirm(build([importable_record(1)]), by=without_p18, file_sha256=SHA)
        assert snapshot() == before

    def test_real_format_today_has_no_importable_row(self, admin):
        """Amb el format real (071) i sense decidir la P-62, cap fila no es pot importar."""
        before = snapshot()
        with pytest.raises(final.FinalImportRefused) as refused:
            final.confirm(sample_file(), by=admin, file_sha256=SHA)
        assert refused.value.code == "rows_unresolved"
        assert refused.value.rows == tuple(range(2, 42))
        with pytest.raises(final.FinalImportRefused) as refused:
            final.confirm(sample_file(), by=admin, file_sha256=SHA, excluded_rows=range(2, 42))
        assert refused.value.code == "nothing_to_import"
        assert snapshot() == before

    def test_a_rejected_file_is_refused(self, admin):
        with pytest.raises(final.FinalImportRefused) as refused:
            final.confirm(b"", by=admin, file_sha256=SHA)
        assert refused.value.code == "empty"

    def test_unknown_excluded_row(self, admin, future_document_rule):
        with pytest.raises(final.FinalImportRefused) as refused:
            final.confirm(
                build([importable_record(1)]), by=admin, file_sha256=SHA, excluded_rows=[9]
            )
        assert (refused.value.code, refused.value.rows) == ("excluded_row_unknown", (9,))

    def test_every_non_importable_row_must_be_excluded(self, admin, future_document_rule):
        data = build([importable_record(1), importable_record(2, {"Nom": ""})])
        before = snapshot()
        with pytest.raises(final.FinalImportRefused) as refused:
            final.confirm(data, by=admin, file_sha256=SHA)
        assert (refused.value.code, refused.value.rows) == ("rows_unresolved", (3,))
        assert snapshot() == before
        batch = final.confirm(data, by=admin, file_sha256=SHA, excluded_rows=[3])
        assert (batch.new_count, batch.excluded_count) == (1, 1)

    def test_an_importable_row_can_be_excluded(self, admin, future_document_rule):
        data = build([importable_record(1), importable_record(2)])
        batch = final.confirm(data, by=admin, file_sha256=SHA, excluded_rows=[2])
        assert Member.objects.get().member_number == 902
        line = batch.lines.get(row=2)
        assert (line.result, line.person) == (ImportLine.Result.EXCLUDED, None)

    def test_a_second_final_import_is_refused(self, admin, future_document_rule):
        final.confirm(build([importable_record(1)]), by=admin, file_sha256=SHA)
        before = snapshot()
        with pytest.raises(final.FinalImportRefused) as refused:
            final.confirm(build([importable_record(2)]), by=admin, file_sha256=SHA)
        assert refused.value.code == "cluber_already_imported"
        assert snapshot() == before

    def test_a_failure_midway_writes_nothing(self, admin, future_document_rule):
        # Dues files amb el mateix `idInterno`: la segona xoca amb l'únic i es desfà tot.
        data = build([importable_record(1), importable_record(2, {"idInterno": "cl-00001"})])
        before = snapshot()
        with pytest.raises(final.FinalImportRefused) as refused:
            final.confirm(data, by=admin, file_sha256=SHA)
        assert refused.value.code == "conflict"
        assert snapshot() == before
        assert MembershipNumberCounter.objects.get().last_number == 0


@allowed
class TestOpenDecisionsKeepRowsOut:
    """P-62 (punts 5 i 6) i P-65 (punt 3): aquestes files no s'importen mai soles."""

    def test_a_row_with_a_document_is_never_imported_without_its_type(
        self, admin, monkeypatch, future_document_rule
    ):
        # Encara que una decisió futura tregui tots els pendents, el document no es perd.
        real = cluber.preview

        def no_pending(data, **kwargs):
            result = real(data, **kwargs)
            for row in result.rows:
                row.pending.clear()
            return result

        monkeypatch.setattr(cluber, "preview", no_pending)
        data = build([importable_record(1, {"Document d'Identitat": dni(1)})])
        with pytest.raises(final.FinalImportRefused) as refused:
            final.confirm(data, by=admin, file_sha256=SHA)
        assert refused.value.code == "rows_unresolved"

    def test_a_row_without_joined_on_is_imported_without_a_date_q075(
        self, admin, future_document_rule
    ):
        # 072, Q-075: cap data inventada; l'entrada inicial porta la data de la importació.
        data = build([importable_record(1, {"Data d'inscripció": ""})])
        final.confirm(data, by=admin, file_sha256=SHA)
        member = Member.objects.get(member_number=901)
        assert member.joined_on is None
        change = member.status_changes.get()
        assert change.origin == MemberStatusChange.Origin.CLUBER_IMPORT
        assert change.effective_on == timezone.localdate()

    def test_a_matching_row_is_not_imported(self, admin, make_person, future_document_rule):
        person = make_person()
        Member.objects.create(
            person=person,
            member_number=901,
            type=MembershipType.objects.get(code="full"),
            joined_on=datetime.date(2020, 1, 1),
        )
        with pytest.raises(final.FinalImportRefused) as refused:
            final.confirm(build([importable_record(1)]), by=admin, file_sha256=SHA)
        assert refused.value.rows == (2,)

    def test_pending_type_is_not_imported(self, admin, future_document_rule):
        data = build([importable_record(1, {"Quota": "Quota familiar 50€."})])
        with pytest.raises(final.FinalImportRefused):
            final.confirm(data, by=admin, file_sha256=SHA)


@allowed
class TestWrites:
    @pytest.fixture
    def batch(self, admin, future_document_rule):
        data = build(
            [
                importable_record(1, {"Ciutat": "Girona", "Data de Naixament": ""}),
                importable_record(2, {cluber.IMAGE_CONSENT: "No", "Quota": "Ple dret 90€"}),
                importable_record(3, {"Nº Soci": "abc"}),  # error
                importable_record(4, {"Email": "", "Nº Soci": "907"}),  # pendent: exclosa
            ]
        )
        return final.confirm(data, by=admin, file_sha256=SHA, excluded_rows=[4, 5])

    def test_batch(self, batch, admin):
        assert batch.kind == ImportBatch.Kind.CLUBER
        assert batch.status == ImportBatch.Status.CONFIRMED
        assert (batch.confirmed_by, batch.created_by, batch.file_sha256) == (admin, admin, SHA)
        assert (batch.new_count, batch.error_count, batch.excluded_count) == (2, 1, 1)
        assert (batch.matching_count, batch.duplicate_count) == (0, 0)

    def test_persons(self, batch):
        first, second = Person.objects.filter(import_batch=batch).order_by("last_name")
        assert first.origin == Person.Origin.CLUBER_IMPORT
        assert (first.first_name, first.last_name) == ("Anna", "Prova1 Exemple")
        assert first.contact_email == "anna1@example.org"
        assert first.address == "Carrer Inventat, 1, 08001 Girona"
        assert first.birth_date is None  # buida: RN-M01-55
        assert second.birth_date == datetime.date(1980, 5, 2)
        assert second.address == "Carrer Inventat, 1, 08001"  # «-» és buida
        assert (first.id_document_type, first.id_document_number) == ("", "")

    def test_members(self, batch):
        members = list(Member.objects.filter(import_batch=batch).order_by("member_number"))
        assert [m.member_number for m in members] == [901, 902]
        assert [m.cluber_id for m in members] == ["cl-00001", "cl-00002"]
        assert [m.type.code for m in members] == ["supporter", "full"]
        assert {m.status for m in members} == {Member.Status.ACTIVE}
        assert {m.joined_on for m in members} == {datetime.date(2010, 3, 15)}
        # Q-076: «Data alta/renovació», d'on compta el carnet [A validar: tresorer].
        assert {m.cluber_renewed_on for m in members} == {datetime.date(2026, 10, 1)}
        seeds = {m.avatar_seed for m in members}
        assert len(seeds) == 2 and all(len(s) == 64 for s in seeds)

    def test_history(self, batch, admin):
        change = MemberStatusChange.objects.get(member__member_number=901)
        assert (change.from_status, change.to_status) == ("", Member.Status.ACTIVE)
        assert change.effective_on == datetime.date(2010, 3, 15)
        assert change.actor_account == admin
        assert change.origin == MemberStatusChange.Origin.CLUBER_IMPORT  # Q-072

    def test_image_consent_only_when_yes(self, batch, admin):
        consent = Consent.objects.get()
        assert consent.person.member.member_number == 901
        assert (consent.channel, consent.action) == (Consent.Channel.CLUBER, Consent.Action.GRANTED)
        assert consent.recorded_by == admin
        text = consent.legal_text
        assert (text.kind, text.language, text.content) == (
            final.IMAGE_CONSENT_KIND,
            "es",
            cluber.IMAGE_CONSENT,
        )

    def test_lines(self, batch):
        lines = {line.row: line for line in batch.lines.all()}
        assert set(lines) == {2, 3, 4, 5}
        assert lines[2].result == lines[3].result == ImportLine.Result.NEW
        assert lines[2].person.member.member_number == 901
        assert (lines[4].result, lines[4].person) == (ImportLine.Result.ERROR, None)
        assert "member_number_invalid" in lines[4].codes
        assert (lines[5].result, lines[5].person) == (ImportLine.Result.EXCLUDED, None)
        assert "email" in lines[5].codes
        for line in lines.values():
            assert set(line.codes) <= set(IMPORT_LINE_CODES)
            assert len(line.codes) == len(set(line.codes))

    def test_counter_continues_after_the_highest_imported(self, batch):
        # CA-M01-22: el número següent serà el més alt importat + 1.
        assert MembershipNumberCounter.objects.get().last_number == 902

    def test_no_fee_charge_or_card(self, batch):
        # RN-M01-33 i 071 (punts 3 i 6): cap quota ni càrrec; el carnet és de la T-M01-19.
        assert Charge.objects.count() == 0
        assert AnnualFee.objects.count() == 0

    def test_audit(self, batch, admin):
        entry = AuditEntry.objects.get(action="members.cluber_import.confirmed")
        assert entry.actor_account == admin
        assert entry.details == {
            "new_count": 2,
            "matching_count": 0,
            "error_count": 1,
            "excluded_count": 1,
            "duplicate_count": 0,
        }


@allowed
def test_counter_is_never_lowered(admin, future_document_rule):
    MembershipNumberCounter.objects.filter(pk=1).update(last_number=5000)
    final.confirm(build([importable_record(1)]), by=admin, file_sha256=SHA)
    assert MembershipNumberCounter.objects.get().last_number == 5000


@allowed
def test_no_iban_reaches_any_table_or_log(admin, future_document_rule, caplog):
    """071, punt 2: la columna d'IBAN es descarta en llegir; després de la importació, cap
    valor inventat d'IBAN no és a cap taula ni als registres del servidor."""
    headers = real_headers()
    records = [
        {**importable_record(n), "IBAN": f"{FALSE_IBAN}{n:012d}", "Nº Soci": str(n)} for n in (1, 2)
    ]
    caplog.set_level(logging.DEBUG)
    batch = final.confirm(build(records, headers), by=admin, file_sha256=SHA)
    assert batch.new_count == 2
    for model in apps.get_models():
        for values in model.objects.values():
            assert FALSE_IBAN not in repr(values), model.__name__
    assert FALSE_IBAN not in caplog.text


class TestImportedText:
    def test_same_content_reuses_the_version_and_a_new_one_is_the_next(self, admin):
        first = consents.imported_text("cluber_images", " Text A ", language="es", by=admin)
        assert (first.version, first.content, first.published_by) == (1, "Text A", admin)
        assert consents.imported_text("cluber_images", "Text A", language="es", by=admin) == first
        second = consents.imported_text("cluber_images", "Text B", language="es", by=admin)
        assert second.version == 2

    def test_an_imported_consent_needs_the_account(self, admin, make_person):
        text = consents.imported_text("cluber_images", "Text A", language="es", by=admin)
        with pytest.raises(ValidationError):
            consents.grant_imported(make_person(), text, by=None)
        assert Consent.objects.count() == 0
