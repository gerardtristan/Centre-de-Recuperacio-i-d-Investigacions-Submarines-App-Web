"""La conciliació d'una transferència també emet `charge.paid` (decisió 049; T-M05b-21, «que la
conciliació també l'emet»). Només dades inventades."""

import pytest

from apps.core import events
from apps.core.models import Event
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.treasury import reconciliation
from apps.treasury.tests.test_reconciliation import charge, lines, ref, treasurer  # noqa: F401

pytestmark = pytest.mark.django_db


def test_confirming_a_transfer_emits_charge_paid_once(treasurer, charge):  # noqa: F811
    quota = charge()
    (line,) = lines(treasurer, (9000, f"TRANSF {ref(quota)} QUOTA"))
    reconciliation.refresh()
    reconciliation.confirm(line, by=treasurer)
    (event,) = Event.objects.filter(name=events.CHARGE_PAID)
    assert event.payload["charge"] == quota.pk and event.payload["amount_cents"] == 9000
