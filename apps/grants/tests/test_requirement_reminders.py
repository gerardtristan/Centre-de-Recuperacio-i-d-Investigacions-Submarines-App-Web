"""T-M09A-15 (avisos): el primer avís d'un requeriment, immediat, i els de 7 i 2 dies abans de la
data límit, que es calculen sobre la data nova si canvia sense repetir els ja enviats
(RN-M09A-19 i 22; CA-M09A-17, 18, 22 i 23). Només dades inventades."""

from datetime import timedelta

import pytest
from django.db import IntegrityError, connection, transaction

from apps.core.models import OutgoingEmail
from apps.grants import reminders
from apps.grants import requirements as r
from apps.grants.models import GrantReminder
from apps.grants.tests.test_justification import granted  # noqa: F401 (fixture)
from apps.grants.tests.test_requirements import D, record
from apps.grants.tests.test_resolution import submitted  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def addresses(treasurer):
    treasurer.notification_email = "tresoreria@example.org"
    treasurer.save()


def sent():
    return list(
        OutgoingEmail.objects.filter(template=reminders.REQUIREMENT_TEMPLATE).values_list(
            "to_address", flat=True
        )
    )


def kinds():
    return list(GrantReminder.objects.values_list("kind", flat=True))


def test_ca_m09a_17_el_primer_avis_en_registrar_lo(granted, treasurer, make_admin):  # noqa: F811
    board = make_admin("board")
    board.notification_email = "junta@example.org"
    board.save()
    record(granted, treasurer, responsible=board.person)
    assert sorted(sent()) == ["junta@example.org", "tresoreria@example.org"]
    assert kinds() == ["requirement_now"]
    body = OutgoingEmail.objects.filter(template=reminders.REQUIREMENT_TEMPLATE).first().body_text
    assert "15/10/2027" in body and "Cal la factura" not in body  # mai la descripció


def test_ca_m09a_18_un_sol_avis_cada_dia_i_cap_si_s_ha_respost(granted, treasurer):  # noqa: F811
    requirement = record(granted, treasurer)
    for _ in range(2):
        reminders.send_due(D - timedelta(days=7))
    assert kinds() == ["requirement_now", "requirement_7"]
    r.answer_requirement(requirement, answered_on=D - timedelta(days=4), by=treasurer)
    for _ in range(2):
        reminders.send_due(D - timedelta(days=2))
    assert kinds() == ["requirement_now", "requirement_7"]
    assert len(sent()) == 2


def test_ca_m09a_22_la_data_nova_recalcula_els_que_falten(granted, treasurer):  # noqa: F811
    requirement = record(granted, treasurer)
    reminders.send_due(D - timedelta(days=7))
    new = D + timedelta(days=10)
    r.change_requirement_due_on(
        requirement, due_on=new, reason="Pròrroga de l'organisme", by=treasurer
    )
    assert reminders.send_due(new - timedelta(days=7)) == 0  # ja enviat
    assert reminders.send_due(D - timedelta(days=2)) == 0  # la data antiga ja no compta
    assert reminders.send_due(new - timedelta(days=2)) == 1
    assert kinds() == ["requirement_now", "requirement_7", "requirement_2"]
    assert GrantReminder.objects.get(kind="requirement_2").due_on == new


def test_ca_m09a_23_la_base_de_dades_rebutja_un_altre_avis_del_mateix_tipus(granted, treasurer):  # noqa: F811
    requirement = record(granted, treasurer)
    reminders.send_due(D - timedelta(days=7))
    with pytest.raises(IntegrityError), transaction.atomic():
        GrantReminder.objects.create(
            application=granted, requirement=requirement, kind="requirement_7", due_on=D
        )
    with pytest.raises(IntegrityError), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO grants_grantreminder"
            " (application_id, requirement_id, kind, due_on, sent_at)"
            " VALUES (%s, %s, 'requirement_7', %s, now())",
            [granted.pk, requirement.pk, D + timedelta(days=10)],
        )


def test_els_dies_dels_requeriments_son_un_ajust(granted, treasurer, monkeypatch):  # noqa: F811
    record(granted, treasurer)
    days = {reminders.REQUIREMENT_DAYS: [5], reminders.DEADLINE_DAYS: [30, 14, 7]}
    monkeypatch.setattr(reminders.business_settings, "get", lambda key, at=None: days[key])
    assert reminders.send_due(D - timedelta(days=7)) == 0
    assert reminders.send_due(D - timedelta(days=5)) == 1
