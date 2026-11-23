"""T-M09-13: avís de marge baix (RN-M09-14, CA-M09-12). Només dades inventades."""

import pytest
from django.db import IntegrityError, transaction

from apps.core import business_settings
from apps.core.models import AppendOnlyError, AuditEntry, OutgoingEmail
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.margins import alerts, planned
from apps.margins.models import LowMarginAlert
from apps.margins.tests.test_planned import activity, boat, treasurer  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db


@pytest.fixture
def addresses(activity, treasurer, make_admin):  # noqa: F811
    activity.responsible.contact_email = "responsable@example.org"
    activity.responsible.save()
    treasurer.notification_email = "tresoreria@example.org"
    treasurer.save()
    secretary = make_admin("secretary")  # sense MG2: no rep l'avís
    secretary.notification_email = "secretaria@example.org"
    secretary.save()


def sent():
    return OutgoingEmail.objects.filter(template=alerts.TEMPLATE)


def test_ca_m09_12_un_sol_avis_al_responsable_i_al_tresorer(activity, treasurer, addresses):  # noqa: F811
    planned.set_planned_cost(activity, boat(), 1000, by=treasurer)  # marge previst −1000
    assert sorted(sent().values_list("to_address", flat=True)) == [
        "responsable@example.org",
        "tresoreria@example.org",
    ]
    email = sent().first()
    assert "Sortida inventada" in email.subject and "-10,00 €" in email.body_text
    assert LowMarginAlert.objects.get().margin_cents == -1000
    assert AuditEntry.objects.get(action=alerts.ALERT_SENT).details["threshold"] == 0

    planned.set_planned_cost(activity, boat(), 1000, by=treasurer, note="La mateixa previsió")
    assert sent().count() == 2  # la previsió no ha canviat: cap avís repetit


def test_una_previsio_nova_per_sota_torna_a_avisar(activity, treasurer, addresses):  # noqa: F811
    planned.set_planned_cost(activity, boat(), 1000, by=treasurer)
    planned.set_planned_cost(activity, boat(), 1500, by=treasurer)
    assert sent().count() == 4
    assert list(LowMarginAlert.objects.values_list("margin_cents", flat=True)) == [-1000, -1500]


def test_al_llindar_o_per_sobre_no_avisa(activity, treasurer, addresses):  # noqa: F811
    planned.set_planned_cost(activity, boat(), 0, by=treasurer)  # marge previst 0 = llindar
    assert not sent().exists()


def test_el_llindar_es_un_ajust(activity, treasurer, addresses, monkeypatch):  # noqa: F811
    assert business_settings.get(alerts.THRESHOLD) == 0  # VC-31: 0 € d'inici
    monkeypatch.setattr(alerts.business_settings, "get", lambda key, at=None: -5000)
    planned.set_planned_cost(activity, boat(), 1000, by=treasurer)
    assert not sent().exists()  # −1000 no és per sota de −5000


def test_treure_un_cost_previst_tambe_comprova_el_marge(activity, treasurer, addresses):  # noqa: F811
    cost = planned.set_planned_cost(activity, boat(), 1000, by=treasurer)
    planned.remove_planned_cost(cost, by=treasurer)  # marge previst 0: cap avís nou
    assert sent().count() == 2


def test_un_avis_sempre_per_sota_del_llindar_i_nomes_insert(activity):  # noqa: F811
    with pytest.raises(IntegrityError), transaction.atomic():
        LowMarginAlert.objects.create(activity=activity, margin_cents=0, threshold_cents=0)
    alert = LowMarginAlert.objects.create(activity=activity, margin_cents=-1, threshold_cents=0)
    with pytest.raises(AppendOnlyError):
        alert.delete()
