"""T-M01-25b: fila de Cluber sense «Data alta/renovació» (097, punt 1) i soci sense document (081,
punt 19). La importació real continua aturada (T-M05a-20): només dades inventades.
"""

import datetime

import pytest
from django.utils import timezone

from apps.core import business_settings
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
TOMORROW = timezone.localdate() + datetime.timedelta(days=1)
SUPPORTER_PRICE = "members.annual_fee_cents.supporter"


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


def test_without_idinterno_the_date_is_not_asked_p397(admin):  # noqa: F811
    row = with_date(1, {"Data alta/renovació": "", "idInterno": ""})
    assert "last_renewal" not in cluber.preview(build([row])).rows[0].pending
    final.confirm(build([row]), by=admin)
    member = Member.objects.get()
    assert (member.cluber_id, member.cluber_renewed_on) == (None, None)
    assert cards.active_card(member) is None


def test_the_audit_counts_are_exact(admin):  # noqa: F811
    rows = [
        with_date(1),
        without_date(2),  # data posada
        without_date(3),  # exclosa només per la data
        with_date(4, {"Data alta/renovació": "", "Nº Soci": "abc"}),  # error: exclosa
        with_date(5, {"Data alta/renovació": "", "Estat": "Baixa"}),  # baixa a Cluber
    ]
    batch = final.confirm(build(rows), by=admin, excluded_rows=[4, 5], renewal_dates={3: SET_ON})
    assert Member.objects.count() == 2
    details = audit_details()
    assert (details["renewal_date_chosen"], details["excluded_without_renewal_date"]) == (1, 1)
    line = batch.lines.get(row=4)
    assert line.result == ImportLine.Result.EXCLUDED
    assert "last_renewal" not in line.codes  # encara no és a la llista tancada de core


@pytest.mark.parametrize(
    ("dates", "code", "rows"),
    [
        ({3: SET_ON}, "renewal_date_row_unknown", (3,)),  # la fila 3 ja porta la data
        ({2: TOMORROW}, "renewal_date_invalid", (2,)),
        ({2: "20/04/2026"}, "renewal_date_invalid", (2,)),
        ({2: datetime.datetime(2026, 4, 20, 10)}, "renewal_date_invalid", (2,)),
        ({2: datetime.date(2009, 1, 1)}, "renewal_date_invalid", (2,)),  # abans de l'alta
    ],
)
def test_wrong_dates_are_refused_and_nothing_is_written(admin, dates, code, rows):  # noqa: F811
    before = snapshot()
    with pytest.raises(final.FinalImportRefused) as refused:
        final.confirm(build([without_date(), with_date(2)]), by=admin, renewal_dates=dates)
    assert (refused.value.code, refused.value.rows) == (code, rows)
    assert snapshot() == before


@pytest.mark.parametrize(
    "values",
    [{"Nº Soci": "abc"}, {"Estat": "Baixa"}, {}],  # error, baixa a Cluber, exclosa
)
def test_a_date_only_for_a_row_that_can_be_imported(admin, values):  # noqa: F811
    rows = [with_date(1), with_date(2, {"Data alta/renovació": "", **values})]
    with pytest.raises(final.FinalImportRefused) as refused:
        final.confirm(build(rows), by=admin, excluded_rows=[3], renewal_dates={3: SET_ON})
    assert (refused.value.code, refused.value.rows) == ("renewal_date_row_unknown", (3,))


def test_the_type_and_the_price_warning_use_the_fee_of_the_date_vc01(admin, make_admin):  # noqa: F811
    yesterday = timezone.localdate() - datetime.timedelta(days=1)
    business_settings.change(SUPPORTER_PRICE, 4000, make_admin("treasurer"), "Prova",
                             effective_from=timezone.localdate())  # fmt: skip
    # Pel preu: 40 € és el simpatitzant d'avui, però no el d'ahir.
    by_price = without_date(1)
    by_price["Quota"], by_price["Preu total"] = "Quota anual 40€", "40"
    assert cluber.preview(build([by_price])).rows[0].member_type == "supporter"
    with pytest.raises(final.FinalImportRefused) as refused:
        final.confirm(build([by_price]), by=admin, renewal_dates={2: yesterday})
    assert (refused.value.code, refused.value.rows) == ("rows_unresolved", (2,))
    # Pel nom: el preu total de 35 € és el d'ahir, i no avisa.
    by_name = with_date(1, {"Data alta/renovació": "", "Preu total": "35"})
    assert "total_price_differs" in cluber.preview(build([by_name])).rows[0].warnings
    batch = final.confirm(build([by_name]), by=admin, renewal_dates={2: yesterday})
    assert "total_price_differs" not in batch.lines.get(row=2).codes


def test_a_date_never_imports_a_member_without_document_081(admin):  # noqa: F811
    row = importable_record(1, {"Data alta/renovació": ""})
    with pytest.raises(final.FinalImportRefused) as refused:
        final.confirm(build([row]), by=admin, renewal_dates={2: SET_ON})
    assert refused.value.code == "rows_unresolved"
    batch = final.confirm(build([row, with_date(2)]), by=admin, excluded_rows=[2])
    assert "id_document" in batch.lines.get(row=2).codes  # el motiu queda a la línia
    assert Member.objects.count() == 1
