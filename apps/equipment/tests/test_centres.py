"""T-M03-05 i T-M03-25: centres de busseig i tarifes amb versions, en qualsevol moment
(RN-M03-06 i 26; CA-M03-05 i 25). Només dades inventades."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.http import Http404

from apps.core.models import AuditEntry, OutgoingEmail
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment import centres
from apps.equipment.models import CentreRate, DiveCentre, EquipmentType

pytestmark = pytest.mark.django_db
TODAY = datetime.date(2027, 3, 1)


@pytest.fixture
def manager(make_admin, monkeypatch):  # noqa: F811
    # MT8 entra al catàleg amb la T-M03-18 (nucli): aquí es dona per fet.
    monkeypatch.setattr(centres, "allowed", lambda by: True)
    treasurer = make_admin("treasurer")
    treasurer.notification_email = "tresoreria@example.org"
    treasurer.save()
    return treasurer


@pytest.fixture
def centre(manager):
    return centres.create_centre(by=manager, name="Centre A", contact_email="info@centre-a.example")


def suit():
    return EquipmentType.objects.get(name="Neoprè")


def add(centre, by, **extra):
    fields = {
        "label": "Equip complet",
        "equipment_type": suit(),
        "cost_cents": 2500,
        "member_price_cents": 3000,
        "valid_from": TODAY,
        "note": "Tarifa del 2027",
        "by": by,
        "today": TODAY,
    }
    return centres.add_rate(centre, **{**fields, **extra})


def test_sense_mt8_al_cataleg_ningu_no_hi_pot_fer_res(make_admin):  # noqa: F811
    assert centres.allowed(make_admin("treasurer")) is False
    with pytest.raises(Http404):
        centres.create_centre(by=make_admin("administrator"), name="Centre B")


def test_un_centre_es_crea_s_edita_i_es_desactiva_pero_no_s_esborra(centre, manager):
    centres.update_centre(centre, by=manager, address="Port inventat")
    centres.update_centre(centre, by=manager, contact_phone="930000000", active=False)
    centre.refresh_from_db()
    assert (centre.active, centre.contact_phone, str(centre)) == (False, "930000000", "Centre A")
    fields = set(
        AuditEntry.objects.filter(action=centres.CENTRE_CHANGED).values_list("field", flat=True)
    )
    assert fields == {"address", "contact_phone", "active"}
    add_rate_to = DiveCentre.objects.create(name="Centre amb tarifes")
    CentreRate.objects.create(
        centre=add_rate_to,
        label="Ampolla",
        cost_cents=1,
        member_price_cents=1,
        valid_from=TODAY,
        created_by=manager,
    )
    with pytest.raises(ProtectedError):
        add_rate_to.delete()


@pytest.mark.parametrize("fields", [{"name": " "}, {"name": "x" * 121}, {"contact_email": "no"}])
def test_dades_del_centre_que_no_valen(manager, fields):
    with pytest.raises((ValidationError, TypeError)):
        centres.create_centre(by=manager, **{"name": "Centre C", **fields})
    with pytest.raises(TypeError):
        centres.create_centre(by=manager, name="Centre D", owner="Persona")


def test_ca_m03_05_una_versio_nova_no_toca_la_vella_i_avisa(centre, manager):
    first = add(centre, manager)
    second = add(centre, manager, cost_cents=2700, valid_from=TODAY + datetime.timedelta(days=30),
                 replaces=first)  # fmt: skip
    first.refresh_from_db()
    assert (first.cost_cents, first.superseded_by) == (2500, second)
    assert centres.rate_on(centre, suit(), TODAY) == first
    assert centres.rate_on(centre, suit(), TODAY + datetime.timedelta(days=30)) == second
    assert str(second).startswith("Centre A: Equip complet")
    assert OutgoingEmail.objects.filter(template="avis-canvi-diners").count() == 2  # RN-AJ-04
    with pytest.raises(ValidationError):  # la vella ja no és la vigent
        add(centre, manager, replaces=first)


@pytest.mark.parametrize(
    "extra",
    [
        {"valid_from": TODAY - datetime.timedelta(days=1)},
        {"note": " "},
        {"label": ""},
        {"cost_cents": -1},
        {"member_price_cents": 1.5},
        {"non_member_price_cents": True},
    ],
)
def test_ca_m03_25_versio_amb_data_passada_sense_nota_o_imports_que_no_valen(
    centre, manager, extra
):
    with pytest.raises(ValidationError):
        add(centre, manager, **extra)
    assert not CentreRate.objects.exists()


def test_ca_m03_25_una_linia_retirada_no_surt_i_un_centre_desactivat_tampoc(centre, manager):
    rate = add(centre, manager, non_member_price_cents=3500)
    with pytest.raises(ValidationError):
        centres.retire_rate(rate, retired_on=TODAY, note="", by=manager, today=TODAY)
    centres.retire_rate(rate, retired_on=TODAY + datetime.timedelta(days=10), note="Ja no en lloga",
                        by=manager, today=TODAY)  # fmt: skip
    assert centres.rate_on(centre, suit(), TODAY + datetime.timedelta(days=9)) == rate
    assert centres.rate_on(centre, suit(), TODAY + datetime.timedelta(days=10)) is None
    with pytest.raises(ValidationError):
        centres.retire_rate(rate, retired_on=TODAY, note="Una altra", by=manager, today=TODAY)
    with pytest.raises(ValidationError):
        add(centre, manager, replaces=rate)
    centres.update_centre(centre, by=manager, active=False)
    centre.refresh_from_db()
    assert centres.rate_on(centre, suit(), TODAY) is None
    with pytest.raises(ValidationError):
        add(centre, manager)


def test_no_es_retira_abans_que_comenci_ni_una_d_un_altre_centre(centre, manager):
    future = add(centre, manager, valid_from=TODAY + datetime.timedelta(days=20))
    with pytest.raises(ValidationError):
        centres.retire_rate(future, retired_on=TODAY + datetime.timedelta(days=5), note="Error",
                            by=manager, today=TODAY)  # fmt: skip
    other = centres.create_centre(by=manager, name="Centre B")
    with pytest.raises(ValidationError):
        add(other, manager, replaces=future)
    assert centres.rate_on(centre, suit(), TODAY) is None  # encara no és vigent


def test_la_base_de_dades_rebutja_retirar_abans_de_l_inici(centre, manager):
    rate = add(centre, manager)
    with pytest.raises(IntegrityError), transaction.atomic():
        CentreRate.objects.filter(pk=rate.pk).update(retired_on=TODAY - datetime.timedelta(days=1))
