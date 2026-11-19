"""T-M01-25b: fila de Cluber sense «Data alta/renovació» (097, punt 1) i soci sense document (081,
punt 19). La importació real continua aturada (T-M05a-20): només dades inventades.
"""

import datetime

import pytest

from apps.core.models import AuditEntry, ImportLine
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import cards
from apps.members.imports import cluber, final
from apps.members.models import Member
from apps.members.tests.test_cluber_final import (  # noqa: F401 (fixtures)
    admin,
    allow,
    importable_record,
    snapshot,
)
from apps.members.tests.test_cluber_preview import build, record

pytestmark = pytest.mark.usefixtures("allow")

SET_ON = datetime.date(2026, 4, 20)  # la data que posa la secretaria (inventada)


def with_date(n=1, values=None):
    """Fila importable: DNI vàlid (tipus deduït), tipus de soci pel nom i `idInterno`."""
    quota = {"Quota": "Quota de soci simpatitzant 35€.", "idInterno": f"cl-{n:05d}"}
    return record(n, {**quota, **(values or {})})


def without_date(n=1):
    return with_date(n, {"Data alta/renovació": ""})


def audit_details():
    return AuditEntry.objects.get(action="members.cluber_import.confirmed").details


def test_a_row_without_the_date_stays_pending(admin):  # noqa: F811
    (row,) = cluber.preview(build([without_date()])).rows
    assert row.pending == ["last_renewal"] and not row.ready
    before = snapshot()
    with pytest.raises(final.FinalImportRefused) as refused:
        final.confirm(build([without_date()]), by=admin)
    assert (refused.value.code, refused.value.rows) == ("rows_unresolved", (2,))
    assert snapshot() == before


def test_the_secretary_sets_the_date_and_the_member_renews_from_it(admin):  # noqa: F811
    final.confirm(build([without_date()]), by=admin, renewal_dates={2: SET_ON})
    member = Member.objects.get()
    assert member.cluber_renewed_on == SET_ON
    loaded = cards.load_member(member.pk)
    assert cards.valid_until(loaded) == datetime.date(2027, 4, 20)
    assert cards.active_card(member) is not None  # T-M01-19b
    assert audit_details()["renewal_date_chosen"] == 1


def test_an_excluded_row_without_the_date_is_counted_but_not_coded(admin):  # noqa: F811
    batch = final.confirm(build([with_date(1), without_date(2)]), by=admin, excluded_rows=[3])
    assert Member.objects.count() == 1
    line = batch.lines.get(row=3)
    assert line.result == ImportLine.Result.EXCLUDED
    assert "last_renewal" not in line.codes  # encara no és a la llista tancada de core
    assert audit_details()["excluded_without_renewal_date"] == 1


@pytest.mark.parametrize(
    ("dates", "code"),
    [
        ({3: SET_ON}, "renewal_date_row_unknown"),  # la fila 3 ja porta la data
        ({2: datetime.date.today() + datetime.timedelta(days=1)}, "renewal_date_invalid"),
        ({2: "20/04/2026"}, "renewal_date_invalid"),
        ({2: datetime.datetime(2026, 4, 20, 10)}, "renewal_date_invalid"),
    ],
)
def test_wrong_dates_are_refused_and_nothing_is_written(admin, dates, code):  # noqa: F811
    before = snapshot()
    with pytest.raises(final.FinalImportRefused) as refused:
        final.confirm(build([without_date(), with_date(2)]), by=admin, renewal_dates=dates)
    assert refused.value.code == code
    assert snapshot() == before


def test_a_date_never_imports_a_member_without_document_081(admin):  # noqa: F811
    row = importable_record(1, {"Data alta/renovació": ""})
    with pytest.raises(final.FinalImportRefused) as refused:
        final.confirm(build([row]), by=admin, renewal_dates={2: SET_ON})
    assert refused.value.code == "rows_unresolved"
    batch = final.confirm(build([row, with_date(2)]), by=admin, excluded_rows=[2])
    assert "id_document" in batch.lines.get(row=2).codes  # el motiu queda a la línia
    assert Member.objects.count() == 1
