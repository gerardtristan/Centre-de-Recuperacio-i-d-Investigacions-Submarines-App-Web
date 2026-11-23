"""T-M09A-06: avisos de la cua — tancament, resposta prevista i justificació, idempotents
(RN-M09A-04, 05, 06 i 20; CA-M09A-01, 02 i 03). Només dades inventades."""

from datetime import date, timedelta

import pytest
from django.db import IntegrityError, transaction

from apps.core.models import AppendOnlyError, OutgoingEmail
from apps.grants import reminders, services
from apps.grants.models import GrantReminder
from apps.grants.tests.test_justification import granted  # noqa: F401 (fixture)
from apps.grants.tests.test_resolution import submitted  # noqa: F401 (fixture)
from apps.grants.tests.test_transitions import SUBMISSION

pytestmark = pytest.mark.django_db
D = date(2027, 4, 30)


@pytest.fixture(autouse=True)
def addresses(treasurer, make_admin):
    treasurer.notification_email = "tresoreria@example.org"
    treasurer.save()
    secretary = make_admin("secretary")  # sense AJ10: no rep cap avís
    secretary.notification_email = "secretaria@example.org"
    secretary.save()


@pytest.fixture
def detected(call, treasurer, general):
    call.closes_on = D
    call.save()
    return services.create_application(
        call, responsible=treasurer.person, department=general, by=treasurer
    )


def emails(template):
    return list(
        OutgoingEmail.objects.filter(template=template).values_list("to_address", flat=True)
    )


def test_ca_m09a_01_un_correu_cada_dia_d_avis_sense_repeticions(detected, make_admin):
    board = make_admin("board")  # la junta responsable rep l'avís pel seu compte
    board.notification_email = "junta@example.org"
    board.save()
    detected.responsible = board.person
    detected.save()
    for days in (30, 14, 7):
        for _ in range(2):  # la tasca s'executa dues vegades el mateix dia
            reminders.send_due(D - timedelta(days=days))
    sent = emails(reminders.CLOSE_TEMPLATE)
    assert sorted(sent) == sorted(["junta@example.org", "tresoreria@example.org"] * 3)
    kinds = list(GrantReminder.objects.values_list("kind", "due_on"))
    assert kinds == [("close_30", D), ("close_14", D), ("close_7", D)]
    body = OutgoingEmail.objects.filter(template=reminders.CLOSE_TEMPLATE).first().body_text
    assert "30/04/2027" in body and "Medi marí" in body and "Diputació Inventada" in body


def test_un_dia_que_no_toca_o_la_data_passada_no_avisen(detected):
    for day in (D - timedelta(days=29), D, D + timedelta(days=1)):
        assert reminders.send_due(day) == 0
    assert not OutgoingEmail.objects.filter(template=reminders.CLOSE_TEMPLATE).exists()


def test_si_la_data_de_tancament_canvia_l_avis_es_calcula_sobre_la_nova(detected, call):
    reminders.send_due(D - timedelta(days=7))
    call.closes_on = D + timedelta(days=10)
    call.save()
    assert reminders.send_due(D - timedelta(days=7)) == 0
    assert reminders.send_due(D + timedelta(days=3)) == 1
    assert GrantReminder.objects.filter(kind="close_7").count() == 2


def test_els_dies_son_un_ajust(detected, monkeypatch):
    monkeypatch.setattr(reminders.business_settings, "get", lambda key, at=None: [10])
    assert reminders.send_due(D - timedelta(days=30)) == 0
    assert reminders.send_due(D - timedelta(days=10)) == 1


def test_ca_m09a_02_una_sollicitud_presentada_no_rep_l_avis_de_tancament(submitted, call):  # noqa: F811
    call.closes_on = D
    call.save()
    reminders.send_due(D - timedelta(days=14))
    assert not OutgoingEmail.objects.filter(template=reminders.CLOSE_TEMPLATE).exists()


def test_ca_m09a_03_avis_el_dia_de_la_resposta_prevista(submitted):  # noqa: F811
    expected = SUBMISSION["submitted_on"] + timedelta(days=90)
    assert submitted.expected_response_on == expected
    assert reminders.send_due(expected - timedelta(days=1)) == 0
    assert reminders.send_due(expected) == 1
    assert reminders.send_due(expected) == 0
    assert emails(reminders.RESPONSE_TEMPLATE) == ["tresoreria@example.org"]


def test_una_concedida_ja_no_rep_l_avis_de_resposta(granted):  # noqa: F811
    assert reminders.send_due(granted.expected_response_on) == 0


def test_avis_de_justificacio_amb_la_proroga_si_n_hi_ha(granted, call):  # noqa: F811
    call.justification_due_on = date(2028, 3, 31)
    call.save()
    assert reminders.send_due(date(2028, 3, 1)) == 1  # 30 dies abans
    granted.justification_extended_to = date(2028, 6, 30)
    granted.save()
    assert reminders.send_due(date(2028, 3, 17)) == 0  # 14 dies abans de la data inicial
    assert reminders.send_due(date(2028, 6, 16)) == 1  # 14 dies abans de la pròrroga
    assert len(emails(reminders.JUSTIFY_TEMPLATE)) == 2


def test_un_avis_que_falla_no_atura_els_altres(detected, call, treasurer, general, monkeypatch):
    other = services.create_application(
        call, responsible=treasurer.person, department=general, by=treasurer
    )
    calls = []

    def flaky(application, **kwargs):
        calls.append(application.pk)
        if application.pk == detected.pk:
            raise RuntimeError("correu caigut (inventat)")
        return True

    monkeypatch.setattr(reminders, "remind", flaky)
    assert reminders.send_due(D - timedelta(days=7)) == 1
    assert sorted(calls) == sorted([detected.pk, other.pk])


def test_restriccions_de_la_base_de_dades(detected):
    GrantReminder.objects.create(application=detected, kind="close_7", due_on=D)
    with pytest.raises(IntegrityError), transaction.atomic():
        GrantReminder.objects.create(application=detected, kind="close_7", due_on=D)
    with (
        pytest.raises(IntegrityError),
        transaction.atomic(),
    ):  # un de requeriment, sense requeriment
        GrantReminder.objects.create(application=detected, kind="requirement_7", due_on=D)
    with pytest.raises(AppendOnlyError):
        GrantReminder.objects.first().delete()
