"""Importació final de Cluber després de la decisió 079 (T-M01-25; A-25, A-26; RN-M01-95;
CA-M01-107 i CA-M01-108): tipus de document triat per la secretaria, empremta canònica que lliga
la prova amb la confirmació, i desfer el lot. Només dades inventades.
"""

import datetime

import pytest
from django.core.exceptions import PermissionDenied

from apps.core.models import AuditEntry, ImportBatch, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import cards
from apps.members.imports import cluber, final
from apps.members.models import Member, MembershipNumberCounter, MemberStatusChange
from apps.members.tests.test_cluber_final import importable_record, snapshot
from apps.members.tests.test_cluber_preview import build

pytestmark = pytest.mark.usefixtures("allow")
REASON = "Importació feta amb el fitxer equivocat (motiu inventat)"
WRONG_LETTER = "12345678A"  # DNI amb la lletra incorrecta: el tipus no es pot deduir
PASSPORT = "PASSAPORT01"


@pytest.fixture
def allow(settings):
    settings.CLUBER_FINAL_IMPORT_ALLOWED = True


@pytest.fixture
def admin(make_admin):  # noqa: F811
    return make_admin("administrator")


def with_document(n, document):
    return importable_record(n, {"Document d'Identitat": document})


# --- CA-M01-107: tipus deduït o triat per la secretaria --------------------------------------


@pytest.mark.django_db
class TestCaM01107DocumentType:
    def test_ca_m01_107_the_secretary_chooses_the_type_row_by_row(self, admin):
        data = build([with_document(1, WRONG_LETTER), with_document(2, PASSPORT)])
        with pytest.raises(final.FinalImportRefused) as refused:
            final.confirm(data, by=admin)
        assert (refused.value.code, refused.value.rows) == ("rows_unresolved", (2, 3))

        batch = final.confirm(data, by=admin, document_types={2: "dni", 3: "passport"})
        people = {
            p.id_document_number: p.id_document_type
            for p in Person.objects.filter(import_batch=batch)
        }
        assert people == {WRONG_LETTER: "dni", PASSPORT: "passport"}
        entry = AuditEntry.objects.get(action="members.cluber_import.confirmed")
        assert (entry.details["document_type_chosen"], entry.details["document_type_deduced"]) == (
            2,
            0,
        )

    def test_ca_m01_107_a_row_without_a_type_is_never_imported(self, admin):
        data = build([with_document(1, WRONG_LETTER), with_document(2, PASSPORT)])
        before = snapshot()
        with pytest.raises(final.FinalImportRefused) as refused:
            final.confirm(data, by=admin, document_types={2: "dni"})
        assert refused.value.rows == (3,)
        assert snapshot() == before
        batch = final.confirm(data, by=admin, document_types={2: "dni"}, excluded_rows=[3])
        assert Person.objects.filter(import_batch=batch).count() == 1

    def test_a_type_for_a_row_that_does_not_need_it_is_refused(self, admin):
        from apps.members.tests.test_cluber_preview import dni

        data = build([with_document(1, dni(1))])
        with pytest.raises(final.FinalImportRefused) as refused:
            final.confirm(data, by=admin, document_types={2: "passport"})
        assert (refused.value.code, refused.value.rows) == ("document_type_row_unknown", (2,))

    def test_an_invalid_type_is_refused(self, admin):
        data = build([with_document(1, WRONG_LETTER)])
        with pytest.raises(final.FinalImportRefused) as refused:
            final.confirm(data, by=admin, document_types={2: "carnet"})
        assert refused.value.code == "document_type_invalid"

    def test_a_deduced_type_is_stored(self, admin):
        from apps.members.tests.test_cluber_preview import dni

        batch = final.confirm(build([with_document(1, dni(1))]), by=admin)
        person = Person.objects.get(import_batch=batch)
        assert (person.id_document_type, person.id_document_number) == ("dni", dni(1))


# --- CA-M01-108: empremta canònica i desfer el lot --------------------------------------------


@pytest.mark.django_db
class TestCaM01108FingerprintAndUndo:
    def test_ca_m01_108_the_batch_keeps_the_canonical_fingerprint(self, admin):
        data = build([with_document(1, PASSPORT)])
        fingerprint = cluber.preview(data).fingerprint
        batch = final.confirm(
            data, by=admin, file_sha256=fingerprint, document_types={2: "passport"}
        )
        assert batch.file_sha256 == fingerprint

    def test_ca_m01_108_a_different_file_from_the_preview_is_refused(self, admin):
        shown = cluber.preview(build([with_document(1, PASSPORT)])).fingerprint
        changed = build([with_document(1, PASSPORT), with_document(2, WRONG_LETTER)])
        before = snapshot()
        with pytest.raises(final.FinalImportRefused) as refused:
            final.confirm(changed, by=admin, file_sha256=shown, document_types={2: "passport"})
        assert refused.value.code == "file_changed"
        assert snapshot() == before

    def test_ca_m01_108_undo_marks_the_batch_and_the_members_leave_keeping_the_numbers(self, admin):
        data = build([with_document(1, PASSPORT), with_document(2, WRONG_LETTER)])
        batch = final.confirm(data, by=admin, document_types={2: "passport", 3: "dni"})
        members = list(Member.objects.filter(import_batch=batch).order_by("pk"))
        numbers = [m.member_number for m in members]
        counter = MembershipNumberCounter.objects.get().last_number
        people = Person.objects.count()

        assert final.undo(batch, by=admin, reason=f"  {REASON}  ") == 2

        batch.refresh_from_db()
        assert batch.status == ImportBatch.Status.UNDONE
        assert (batch.undone_by, batch.undone_at is not None) == (admin, True)
        for member in Member.objects.filter(pk__in=[m.pk for m in members]):
            assert member.status == Member.Status.LEFT
            assert member.left_on == datetime.date.today() or member.left_on is not None
            change = MemberStatusChange.objects.filter(member=member).order_by("-pk").first()
            assert (change.to_status, change.reason) == (Member.Status.LEFT, REASON)
        assert [
            m.member_number for m in Member.objects.filter(import_batch=batch).order_by("pk")
        ] == numbers
        assert MembershipNumberCounter.objects.get().last_number == counter  # cap número lliure
        assert Person.objects.count() == people  # cap persona esborrada
        entry = AuditEntry.objects.get(action=final.UNDONE)
        assert (entry.actor_account, entry.reason, entry.details) == (
            admin,
            REASON,
            {"members_left": 2},
        )

    def test_undo_revokes_the_card_issued_by_the_import(self, admin):
        batch = final.confirm(
            build([with_document(1, PASSPORT)]), by=admin, document_types={2: "passport"}
        )
        member = Member.objects.get(import_batch=batch)
        assert cards.active_card(member)  # T-M01-19b
        final.undo(batch, by=admin, reason=REASON)
        assert not cards.active_card(member)

    def test_undo_needs_a_reason_p18_a_confirmed_batch_and_the_option(
        self,
        admin,
        make_admin,  # noqa: F811
        settings,
    ):
        batch = final.confirm(
            build([with_document(1, PASSPORT)]), by=admin, document_types={2: "passport"}
        )
        with pytest.raises(final.FinalImportRefused) as refused:
            final.undo(batch, by=admin, reason="  ")
        assert refused.value.code == "reason_required"
        with pytest.raises(PermissionDenied):
            final.undo(batch, by=make_admin("secretary"), reason=REASON)
        final.undo(batch, by=admin, reason=REASON)
        with pytest.raises(final.FinalImportRefused) as refused:
            final.undo(batch, by=admin, reason=REASON)
        assert refused.value.code == "not_undoable"
        settings.CLUBER_FINAL_IMPORT_ALLOWED = False
        with pytest.raises(final.FinalImportBlocked):
            final.undo(batch, by=admin, reason=REASON)
        assert Member.objects.get(import_batch=batch).status == Member.Status.LEFT

    def test_after_undo_the_same_rows_match_the_members_that_left(self, admin):
        """Amb el lot desfet es pot tornar a provar, però la fila ja no és nova: coincideix amb
        el soci que s'ha donat de baixa (mateix número, 039) i s'ha d'excloure; mai no se'n
        crea cap altre amb el mateix número."""
        data = build([with_document(1, PASSPORT)])
        batch = final.confirm(data, by=admin, document_types={2: "passport"})
        member = Member.objects.get(import_batch=batch)
        final.undo(batch, by=admin, reason=REASON)
        result = cluber.preview(data)
        assert result.rejected is None  # ja no hi ha cap lot confirmat
        (row,) = result.rows
        assert (row.identity, row.member_id) == ("matching", member.pk)
        with pytest.raises(final.FinalImportRefused) as refused:
            final.confirm(data, by=admin, document_types={2: "passport"})
        assert refused.value.rows == (2,)
        assert Member.objects.filter(member_number=member.member_number).count() == 1
