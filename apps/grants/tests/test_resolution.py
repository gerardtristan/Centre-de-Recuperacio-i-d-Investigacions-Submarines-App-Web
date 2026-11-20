"""T-M09A-07: resolució concedida i denegada amb observacions (P-M09A-E; RN-M09A-08 i 13;
CA-M09A-07). Només dades inventades."""

import uuid
from datetime import date

import pytest
from django.db import IntegrityError, transaction
from django.http import Http404

from apps.core.models import AppendOnlyError, PrivateFile
from apps.grants import services
from apps.grants.models import DenialNote, GrantApplication
from apps.grants.tests.test_transitions import SUBMISSION, prepared, ready_all

pytestmark = pytest.mark.django_db
S = GrantApplication.Status
RESOLVED = date(2027, 6, 1)


def resolution(person):
    return PrivateFile.objects.create(
        storage_key=f"prova-{uuid.uuid4().hex}",
        kind=PrivateFile.Kind.PAYMENT_PROOF,  # el tipus del document és de la T-M09-25
        owner=person,
        content_type="application/pdf",
        size_bytes=10,
        download_name="resolucio.pdf",
    )


@pytest.fixture
def submitted(call, treasurer, general):
    application = services.create_application(
        call, responsible=treasurer.person, department=general, by=treasurer
    )
    prepared(application, call, treasurer)
    ready_all(application, treasurer)
    return services.transition(application, S.SUBMITTED, by=treasurer, **SUBMISSION)


def grant(application, by, **extra):
    data = {
        "resolved_on": RESOLVED,
        "resolution_file": resolution(by.person),
        "amount_granted_cents": 240000,
        **extra,
    }
    return services.transition(application, S.GRANTED, by=by, **data)


def deny(application, by, reason="Fora de termini", **extra):
    data = {
        "resolved_on": RESOLVED,
        "resolution_file": resolution(by.person),
        "improvements": "Presentar-la abans",
        **extra,
    }
    return services.transition(application, S.DENIED, by=by, reason=reason, **data)


def test_concedida_amb_import_data_i_resolucio(submitted, treasurer):
    granted = grant(submitted, treasurer)
    assert (granted.status, granted.amount_granted_cents, granted.resolved_on) == (
        S.GRANTED,
        240000,
        RESOLVED,
    )
    assert granted.granted_over_requested is False  # L-M09A-03: menys del demanat


def test_mes_del_demanat_es_un_avis_i_no_bloqueja(submitted, treasurer):
    assert grant(submitted, treasurer, amount_granted_cents=350000).granted_over_requested


@pytest.mark.parametrize(
    "extra",
    [
        {"resolved_on": None},
        {"resolution_file": None},
        {"amount_granted_cents": None},
        {"amount_granted_cents": -1},
    ],
)
def test_concedir_sense_les_dades_es_rebutja(submitted, treasurer, extra):
    with pytest.raises(services.GrantError):
        grant(submitted, treasurer, **extra)
    submitted.refresh_from_db()
    assert submitted.status == S.SUBMITTED


def test_denegada_amb_observacio_i_despres_tancada(submitted, treasurer):
    denied = deny(submitted, treasurer)
    note = DenialNote.objects.get(application=denied)
    assert (note.reason, note.improvements, note.resolved_on) == (
        "Fora de termini",
        "Presentar-la abans",
        RESOLVED,
    )
    assert services.transition(denied, S.CLOSED, by=treasurer).status == S.CLOSED


@pytest.mark.parametrize(
    ("reason", "extra"), [(" ", {}), ("Fora de termini", {"improvements": ""})]
)
def test_ca_m09a_07_denegar_sense_observacio_es_rebutja(submitted, treasurer, reason, extra):
    with pytest.raises(services.GrantError):
        deny(submitted, treasurer, reason=reason, **extra)
    assert not DenialNote.objects.exists()


def test_l_observacio_nomes_s_afegeix_i_es_completa(submitted, treasurer):
    note = DenialNote.objects.get(application=deny(submitted, treasurer))
    with pytest.raises(AppendOnlyError):
        note.delete()
    with pytest.raises(IntegrityError), transaction.atomic():
        DenialNote.objects.create(
            application=submitted,
            reason="",
            resolved_on=RESOLVED,
            improvements="",
            recorded_by=treasurer,
        )


def test_concedida_no_es_tanca_directament(submitted, treasurer):
    granted = grant(submitted, treasurer)
    with pytest.raises(services.InvalidTransition):  # L-M09A-04: es fa amb el desfer
        services.transition(granted, S.CLOSED, by=treasurer, reason="Renúncia")


def test_resoldre_demana_aj5_i_la_junta_nomes_les_seves(submitted, make_admin):
    with pytest.raises(Http404):
        grant(submitted, make_admin("secretary"))
    with pytest.raises(Http404):
        grant(submitted, make_admin("board"))  # no n'és responsable


def test_tancar_una_denegada_demana_aj8(submitted, treasurer, make_admin):
    denied = deny(submitted, treasurer)
    with pytest.raises(Http404):
        services.transition(denied, S.CLOSED, by=make_admin("board"))
