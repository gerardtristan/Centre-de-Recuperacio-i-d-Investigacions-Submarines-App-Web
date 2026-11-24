"""Lot i línia d'importació (T-M01-24): contracte compartit de la 00.

Precisions: files de la T-M01-24 a docs/planning.md#ajustos-060-lectura (contracte compartit del
lot, línia d'importació, procedència i proteccions). Cada restricció es prova amb una escriptura
que arriba a la base de dades i comprova quina restricció la rebutja; cada cas parteix de dades
que compleixen totes les altres. Només dades inventades.
"""

import datetime
import hashlib

import pytest
from django.db import DataError, IntegrityError, connection, models, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models import ProtectedError
from django.db.models.deletion import Collector
from django.utils import timezone

from apps.core import imports
from apps.core.models import (
    IMPORT_LINE_CODES,
    ImportBatch,
    ImportLine,
    RolePermission,
    UndeletableError,
)
from apps.members.models import LicenceRecord, Member, MembershipType
from conftest import CommittedDataTestCase, committed_snapshot, delete_committed_rows

SHA = hashlib.sha256(b"fitxer-inventat").hexdigest()
HOUR = datetime.timedelta(hours=1)


def later():
    """Posterior a totes les dates que posa `make_batch` (base + 2 hores com a màxim)."""
    return timezone.now() + datetime.timedelta(days=1)


def _db_error(make, error):
    with pytest.raises(error) as info, transaction.atomic():
        make()
    return info.value.__cause__  # l'error de psycopg, amb el diagnòstic de PostgreSQL


def rejected(make, constraint):
    """Rebutjat per la restricció CHECK o única indicada (nom que dona PostgreSQL)."""
    assert _db_error(make, IntegrityError).diag.constraint_name == constraint


def rejected_not_null(make, column):
    cause = _db_error(make, IntegrityError)
    assert (cause.sqlstate, cause.diag.column_name) == ("23502", column)


def rejected_too_long(make):
    assert _db_error(make, DataError).sqlstate == "22001"  # text més llarg que la columna


@pytest.fixture
def make_batch(admin_account):
    def make(status=ImportBatch.Status.CONFIRMED, kind=ImportBatch.Kind.CLUBER, **fields):
        # Un sol instant per a totes les dates (sense crides separades a now()).
        base = timezone.now()
        values = {
            "kind": kind,
            "status": status,
            "file_sha256": SHA,
            "created_by": admin_account,
            "created_at": base,
        }
        if status in (ImportBatch.Status.CONFIRMED, ImportBatch.Status.UNDONE):
            values.update(confirmed_by=admin_account, confirmed_at=base + HOUR)
        if status == ImportBatch.Status.UNDONE:
            values.update(undone_by=admin_account, undone_at=base + 2 * HOUR)
        values.update(fields)
        return ImportBatch.objects.create(**values)

    return make


@pytest.fixture
def batch(make_batch):
    return make_batch()


class TestImportBatch:
    @pytest.mark.parametrize("status", ["preview", "confirmed", "undone", "rejected"])
    @pytest.mark.parametrize("kind", ["cluber", "bank_statement"])
    def test_every_state_and_kind(self, make_batch, kind, status):
        batch = make_batch(status, kind)
        batch.refresh_from_db()
        assert (batch.kind, batch.status) == (kind, status)
        counts = (
            batch.new_count,
            batch.matching_count,
            batch.error_count,
            batch.excluded_count,
            batch.duplicate_count,
        )
        assert counts == (0, 0, 0, 0, 0)
        assert batch.created_at is not None

    def test_unknown_kind(self, make_batch):
        rejected(lambda: make_batch(kind="altre"), "importbatch_kind_valid")

    def test_unknown_status(self, make_batch):
        # Un estat desconegut no compleix mai `status_fields`, que PostgreSQL comprova abans
        # (ordre alfabètic dels noms): `status_valid` queda coberta per aquesta.
        rejected(lambda: make_batch(status="altre"), "importbatch_status_fields")

    @pytest.mark.parametrize("sha", [SHA.upper(), SHA[:-1], "g" * 64, ""])
    def test_sha256_format(self, make_batch, sha):
        rejected(lambda: make_batch(file_sha256=sha), "importbatch_sha256_format")

    def test_sha256_too_long(self, make_batch):
        rejected_too_long(lambda: make_batch(file_sha256=SHA + "0"))

    @pytest.mark.parametrize(
        "field", ["new_count", "matching_count", "error_count", "excluded_count", "duplicate_count"]
    )
    def test_counts_not_negative(self, make_batch, field):
        rejected(lambda: make_batch(**{field: -1}), f"core_importbatch_{field}_check")
        assert getattr(make_batch(ImportBatch.Status.PREVIEW, **{field: 7}), field) == 7

    def test_creation_is_required(self, make_batch):
        rejected_not_null(lambda: make_batch(created_by=None), "created_by_id")
        batch = make_batch()
        update = ImportBatch.objects.filter(pk=batch.pk).update
        rejected_not_null(lambda: update(created_at=None), "created_at")

    def test_confirmation_actor_and_date_together(self, make_batch, admin_account):
        # Data sense actor (l'estat confirmat ja té la data) i actor sense data (en
        # previsualització, l'estat no en demana cap).
        rejected(lambda: make_batch(confirmed_by=None), "importbatch_confirmed_pair")
        rejected(
            lambda: make_batch(ImportBatch.Status.PREVIEW, confirmed_by=admin_account),
            "importbatch_confirmed_pair",
        )

    def test_undo_actor_and_date_together(self, make_batch, admin_account):
        rejected(
            lambda: make_batch(ImportBatch.Status.UNDONE, undone_by=None),
            "importbatch_undone_pair",
        )
        rejected(
            lambda: make_batch(ImportBatch.Status.PREVIEW, undone_by=admin_account),
            "importbatch_undone_pair",
        )

    def test_p445_mark_undone_sets_who_and_when(self, make_batch, admin_account):
        past = timezone.now() - 2 * HOUR  # la fixture confirma una hora després de crear
        batch = make_batch(created_at=past, confirmed_at=past + HOUR)
        batch = imports.mark_undone(batch, by=admin_account)
        batch.refresh_from_db()
        assert (batch.status, batch.undone_by) == (ImportBatch.Status.UNDONE, admin_account)
        assert batch.undone_at >= batch.confirmed_at

    @pytest.mark.parametrize("status", ["preview", "undone", "rejected"])
    def test_p445_only_a_confirmed_batch_is_undone(self, make_batch, admin_account, status):
        batch = make_batch(status)
        with pytest.raises(ValueError):
            imports.mark_undone(batch, by=admin_account)
        batch.refresh_from_db()
        assert batch.status == status

    @pytest.mark.parametrize("status", ["preview", "rejected"])
    def test_preview_and_rejected_carry_no_confirmation_or_undo(
        self, make_batch, admin_account, status
    ):
        moment = later()
        confirmation = {"confirmed_by": admin_account, "confirmed_at": moment}
        undo = {"undone_by": admin_account, "undone_at": moment}
        for fields in (confirmation, undo, {**confirmation, **undo}):
            rejected(lambda f=fields: make_batch(status, **f), "importbatch_status_fields")

    def test_confirmed_needs_confirmation_and_no_undo(self, make_batch, admin_account):
        rejected(
            lambda: make_batch(confirmed_by=None, confirmed_at=None), "importbatch_status_fields"
        )
        rejected(
            lambda: make_batch(undone_by=admin_account, undone_at=later()),
            "importbatch_status_fields",
        )

    def test_undone_needs_confirmation_and_undo(self, make_batch):
        status = ImportBatch.Status.UNDONE
        rejected(
            lambda: make_batch(status, confirmed_by=None, confirmed_at=None),
            "importbatch_status_fields",
        )
        rejected(
            lambda: make_batch(status, undone_by=None, undone_at=None),
            "importbatch_status_fields",
        )

    def test_dates_in_order(self, make_batch):
        yesterday = timezone.now() - datetime.timedelta(days=1)
        rejected(lambda: make_batch(confirmed_at=yesterday), "importbatch_confirmed_after_created")
        rejected(
            lambda: make_batch(ImportBatch.Status.UNDONE, undone_at=yesterday),
            "importbatch_undone_after_confirmed",
        )
        # El mateix instant per a les tres dates s'accepta (≥, no >).
        moment = timezone.now()
        same = make_batch(
            ImportBatch.Status.UNDONE, created_at=moment, confirmed_at=moment, undone_at=moment
        )
        assert same.created_at == same.confirmed_at == same.undone_at

    def test_confirmation_a_microsecond_before_creation_is_rejected(self, make_batch):
        # El cas del CI #92: la restricció no té cap tolerància.
        moment = timezone.now()
        before = moment - datetime.timedelta(microseconds=1)
        rejected(
            lambda: make_batch(created_at=moment, confirmed_at=before),
            "importbatch_confirmed_after_created",
        )

    @pytest.mark.parametrize("status", ["preview", "confirmed", "undone", "rejected"])
    def test_fixture_chronology(self, make_batch, status):
        # Regressió del CI #92 i #93: cronologia determinista, sense dependre del rellotge.
        batch = make_batch(status)
        batch.refresh_from_db()
        if batch.confirmed_at:
            assert batch.confirmed_at - batch.created_at == HOUR
        if batch.undone_at:
            assert batch.undone_at - batch.confirmed_at == HOUR

    def test_only_one_confirmed_cluber_batch(self, make_batch):
        make_batch()
        rejected(make_batch, "importbatch_one_confirmed_cluber")
        make_batch(ImportBatch.Status.UNDONE)
        make_batch(ImportBatch.Status.PREVIEW)
        make_batch(ImportBatch.Status.REJECTED)
        make_batch(kind=ImportBatch.Kind.BANK_STATEMENT)
        make_batch(kind=ImportBatch.Kind.BANK_STATEMENT)  # la T-M00-01 en decidirà les regles

    def test_cannot_be_deleted(self, batch):
        with pytest.raises(UndeletableError):
            batch.delete()
        with pytest.raises(UndeletableError):
            ImportBatch.objects.all().delete()
        assert ImportBatch.objects.filter(pk=batch.pk).exists()

    def test_account_relations_are_protect(self):
        for name in ("created_by", "confirmed_by", "undone_by"):
            field = ImportBatch._meta.get_field(name)
            assert field.remote_field.on_delete is models.PROTECT

    def test_no_iban_field(self):
        for model in (ImportBatch, ImportLine):
            assert not [f.name for f in model._meta.get_fields() if "iban" in f.name.lower()]


class TestImportLine:
    def test_defaults(self, batch):
        line = ImportLine.objects.create(batch=batch, row=2, result=ImportLine.Result.NEW)
        line.refresh_from_db()
        assert (line.codes, line.person) == ([], None)
        other = ImportLine.objects.create(batch=batch, row=3, result=ImportLine.Result.NEW)
        assert other.codes is not line.codes  # llista nova a cada fila

    def test_unique_row_per_batch(self, batch, make_batch):
        ImportLine.objects.create(batch=batch, row=2, result=ImportLine.Result.NEW)
        rejected(
            lambda: ImportLine.objects.create(batch=batch, row=2, result="new"),
            "importline_unique_row",
        )
        other = make_batch(ImportBatch.Status.PREVIEW)
        ImportLine.objects.create(batch=other, row=2, result=ImportLine.Result.NEW)

    def test_row_at_least_one(self, batch):
        create = ImportLine.objects.create
        rejected(lambda: create(batch=batch, row=0, result="new"), "importline_row_positive")
        # Un negatiu també incompleix la de `PositiveIntegerField`, que PostgreSQL comprova abans.
        rejected(lambda: create(batch=batch, row=-1, result="new"), "core_importline_row_check")

    def test_unknown_result(self, batch):
        rejected(
            lambda: ImportLine.objects.create(batch=batch, row=2, result="altre"),
            "importline_result_valid",
        )

    @pytest.mark.parametrize("result", ["error", "excluded", "duplicate"])
    def test_no_person_on_lines_that_create_nothing(self, batch, make_person, result):
        person = make_person()
        rejected(
            lambda: ImportLine.objects.create(batch=batch, row=2, result=result, person=person),
            "importline_person_only_new_or_matching",
        )
        ImportLine.objects.create(batch=batch, row=2, result=result)

    @pytest.mark.parametrize("result", ["new", "matching"])
    def test_person_on_new_and_matching_lines(self, batch, make_person, result):
        line = ImportLine.objects.create(batch=batch, row=2, result=result, person=make_person())
        assert line.person_id is not None

    def test_relations_are_protect(self):
        for name in ("batch", "person"):
            field = ImportLine._meta.get_field(name)
            assert field.remote_field.on_delete is models.PROTECT

    def test_cannot_be_deleted(self, batch):
        line = ImportLine.objects.create(batch=batch, row=2, result=ImportLine.Result.NEW)
        with pytest.raises(UndeletableError):
            line.delete()
        with pytest.raises(UndeletableError):
            ImportLine.objects.all().delete()


class TestClosedCodes:
    @pytest.fixture
    def line(self, batch):
        return ImportLine.objects.create(batch=batch, row=2, result=ImportLine.Result.ERROR)

    def _set(self, line, codes):
        ImportLine.objects.filter(pk=line.pk).update(codes=codes)

    def test_valid_codes_and_empty_list(self, line):
        for codes in ([], ["field_count"], sorted(IMPORT_LINE_CODES)):
            self._set(line, codes)
            line.refresh_from_db()
            assert line.codes == codes

    @pytest.mark.parametrize(
        "codes",
        [
            ["codi_desconegut"],
            ["field_count", "codi_desconegut"],
            ["ES0000000000000000000000"],  # text amb forma d'IBAN: no és a la llista
            ["Field_Count"],
            ["field_count "],
            [""],
            [None],
            ["field_count", None],
            [["field_count"]],  # Django el converteix en el text "['field_count']"
        ],
    )
    def test_anything_else_is_rejected(self, line, codes):
        rejected(lambda: self._set(line, codes), "importline_codes_closed_list")
        line.refresh_from_db()
        assert line.codes == []

    def test_free_text_longer_than_a_code_is_rejected(self, line):
        # Django envia la llista amb una conversió explícita a varchar(40)[], i PostgreSQL hi
        # retalla el text a 40 caràcters en lloc de donar un error de llargada; el rebuig és de
        # la llista tancada. Cap codi no fa 40 caràcters: un text retallat no en pot ser cap.
        assert max(map(len, IMPORT_LINE_CODES)) < 40
        rejected(lambda: self._set(line, ["x" * 41]), "importline_codes_closed_list")

    def test_null_list_is_rejected(self, line):
        rejected_not_null(lambda: self._set(line, None), "codes")

    @pytest.mark.parametrize(
        ("sql_value", "constraint"),
        [
            ("ARRAY[['field_count']]::varchar(40)[]", "importline_codes_one_dimension"),
            ("'[0:0]={field_count}'::varchar(40)[]", "importline_codes_one_dimension"),
            ("ARRAY[NULL]::varchar(40)[]", "importline_codes_closed_list"),
        ],
    )
    def test_unexpected_structures_rejected_by_the_database(self, line, sql_value, constraint):
        # Sense passar pel camp de Django: la restricció és de la base de dades.
        def update():
            with connection.cursor() as cursor:
                cursor.execute(
                    f"UPDATE core_importline SET codes = {sql_value} WHERE id = %s",  # noqa: S608
                    [line.pk],
                )

        rejected(update, constraint)


class TestProvenance:
    @pytest.fixture
    def supporter(self, db):
        return MembershipType.objects.get(code="supporter")

    def test_import_batch_is_empty_by_default(self, make_person, supporter):
        person = make_person()
        member = Member.objects.create(person=person, type=supporter, joined_on=timezone.now())
        licence = LicenceRecord.objects.create(
            member=member, licence_type="Inventada", issued_on=timezone.now(), source="manual"
        )
        for record in (person, member, licence):
            record.refresh_from_db()
            assert record.import_batch is None

    def test_import_batch_protects_the_batch_not_the_record(self, batch, make_person, supporter):
        person = make_person(import_batch=batch)
        member = Member.objects.create(
            person=make_person(), type=supporter, joined_on=timezone.now(), import_batch=batch
        )
        licence = LicenceRecord.objects.create(
            member=member,
            licence_type="Inventada",
            issued_on=timezone.now(),
            source="cluber",
            import_batch=batch,
        )
        # El lot no es pot esborrar mentre hi hagi registres que el referencien.
        with pytest.raises(ProtectedError):
            Collector(using="default").collect([batch])
        # La referència no protegeix el registre (esborrar-lo no és el desfer, que és de la
        # T-M01-25): la política d'esborrat és la de cada model.
        licence.delete()
        person.delete()
        assert ImportBatch.objects.filter(pk=batch.pk).exists()

    def test_line_person_protects_the_person(self, batch, make_person):
        person = make_person()
        ImportLine.objects.create(batch=batch, row=2, result="matching", person=person)
        with pytest.raises(ProtectedError):
            person.delete()
        with pytest.raises(ProtectedError):
            Collector(using="default").collect([batch])  # la línia també protegeix el lot


def _applied_targets():
    """Per a cada app, la darrera migració aplicada: l'estat complet de la base de proves."""
    loader = MigrationExecutor(connection).loader
    applied = {key for key in loader.applied_migrations if key in loader.graph.node_map}
    targets = [
        key
        for key in applied
        if not any(c in applied and c[0] == key[0] for c in loader.graph.node_map[key].children)
    ]
    return applied, targets


class TestMigrationsAreReversible(CommittedDataTestCase):
    """Les migracions d'aquesta tanda es desfan i es tornen a aplicar a la base de proves.

    Es restaura sempre l'estat d'abans (totes les apps, també les que en depenguin), encara que
    falli una comprovació.
    """

    def _restore(self, targets):
        """Torna a l'estat d'abans i fa una foto nova de les claus: desfer i refer les migracions
        torna a crear les seves dades (rols, matriu, ajustos) amb claus noves, i la neteja de
        `CommittedDataTestCase` les esborraria i deixaria la base sense permisos per a les proves
        que vénen després (TestConcurrentEnrolments, «no trobat»)."""
        MigrationExecutor(connection).migrate(targets)
        self._tables, self._start = committed_snapshot()

    def test_migration_data_survives_the_cleanup(self):
        cells = RolePermission.objects.count()
        applied, targets = _applied_targets()
        try:
            MigrationExecutor(connection).migrate([("core", "0009_private_files")])
        finally:
            self._restore(targets)
        delete_committed_rows(self._tables, self._start)  # la neteja del final de la prova
        assert RolePermission.objects.count() == cells

    def test_backwards_and_forwards(self):
        applied, targets = _applied_targets()
        try:
            MigrationExecutor(connection).migrate(
                [("members", "0005_member_avatar_seed_format"), ("core", "0009_private_files")]
            )
            tables = connection.introspection.table_names()
            assert "core_importbatch" not in tables and "core_importline" not in tables
            MigrationExecutor(connection).migrate(targets)
            tables = connection.introspection.table_names()
            assert "core_importbatch" in tables and "core_importline" in tables
            with connection.cursor() as cursor:
                for table in ("core_person", "members_member", "members_licencerecord"):
                    columns = connection.introspection.get_table_description(cursor, table)
                    assert "import_batch_id" in [c.name for c in columns]
        finally:
            self._restore(targets)
        assert _applied_targets()[0] == applied
