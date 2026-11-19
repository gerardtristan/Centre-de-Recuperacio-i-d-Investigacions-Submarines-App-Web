"""T-M01-18c: venciment de la quota d'un soci importat de Cluber, de cap a cap (097, punt 1).

De la importació final a la quota de renovació: 12 mesos des de «Data alta/renovació». Només
dades inventades; la importació real continua aturada (T-M05a-20).
"""

import datetime

import pytest

from apps.core.models import Charge
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import cards, fees
from apps.members.imports import final
from apps.members.models import AnnualFee, Member
from apps.members.tests.test_cluber_final import admin, allow  # noqa: F401 (fixtures)
from apps.members.tests.test_cluber_preview import build, record

RENEWED = datetime.date(2026, 10, 1)  # «Data alta/renovació» de `record`
DUE = datetime.date(2027, 10, 1)


@pytest.mark.usefixtures("allow")
def test_imported_member_renews_twelve_months_after_cluber(admin):  # noqa: F811
    row = record(1, {"Quota": "Quota de soci simpatitzant 35€.", "idInterno": "cl-00001"})
    final.confirm(build([row]), by=admin)
    member = Member.objects.get(cluber_id="cl-00001")
    assert member.cluber_renewed_on == RENEWED
    assert cards.valid_until(cards.load_member(member.pk)) == DUE

    lead = datetime.timedelta(days=fees._lead_days())
    assert fees.generate_due_fees(DUE - lead - datetime.timedelta(days=1)) == []
    (fee,) = fees.generate_due_fees(DUE - lead)
    assert (fee.member, fee.period, fee.due_on) == (member, 2027, DUE)
    assert fee.charge.amount_cents == member.type.annual_fee_cents
    assert fee.charge.status == Charge.Status.PENDING
    assert AnnualFee.objects.count() == 1  # cap quota en importar (RN-M01-33)
