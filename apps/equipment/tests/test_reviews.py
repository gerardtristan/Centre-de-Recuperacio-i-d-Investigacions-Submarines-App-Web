"""T-M03-14: revisions del material, peces que vencen i revisió fallida (RN-M03-15; CA-M03-12).
Només dades inventades."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404

from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment import access, inventory, reviews
from apps.equipment.models import EquipmentItem, EquipmentReview, EquipmentType

pytestmark = pytest.mark.django_db
TODAY = datetime.date(2027, 6, 1)


@pytest.fixture
def manager(make_admin, monkeypatch):  # noqa: F811
    monkeypatch.setattr(access, "allowed", lambda by, code, obj=None: True)  # MT3, MT11
    return make_admin("equipment_manager")


def tank(by, review_on=TODAY + datetime.timedelta(days=60)):
    return inventory.create_item(
        equipment_type=EquipmentType.objects.get(name="Ampolla"),
        litres=12,
        next_review_on=review_on,
        by=by,
    )


def schedule(item, by, **extra):
    fields = {"kind": "hydrostatic_test", "due_on": TODAY, "by": by, "provider": "Taller inventat"}
    return reviews.schedule_review(item, **{**fields, **extra})


def test_revisio_correcta_la_peca_torna_amb_la_propera_data(manager):
    item = tank(manager)
    review = schedule(item, manager)
    reviews.send_review(review, sent_on=TODAY, by=manager)
    assert EquipmentItem.objects.get(pk=item.pk).status == "in_review"
    closed = reviews.close_review(
        review,
        done_on=TODAY + datetime.timedelta(days=3),
        result="ok",
        cost_cents=4500,
        next_review_on=datetime.date(2028, 6, 1),
        notes="Sense incidències",
        by=manager,
    )
    item.refresh_from_db()
    assert (item.status, item.next_review_on) == ("available", datetime.date(2028, 6, 1))
    assert (closed.result, closed.notes) == ("ok", "Sense incidències")
    assert str(closed).startswith(f"{item.code} Prova hidràulica")
    assert list(reviews.reviews_with_cost(TODAY, TODAY + datetime.timedelta(days=5))) == [closed]
    with pytest.raises(ValidationError):  # una revisió tancada no es modifica
        reviews.send_review(review, sent_on=TODAY, by=manager)


def test_ca_m03_12_una_revisio_fallida_dona_de_baixa_la_peca_amb_el_motiu(manager):
    item = tank(manager)
    review = schedule(item, manager)
    reviews.close_review(review, done_on=TODAY, result="failed", by=manager)
    item.refresh_from_db()
    assert item.status == "retired"
    assert item.retired_reason == "Revisió fallida (Prova hidràulica) del 01/06/2027"


def test_una_peca_d_un_tipus_sense_revisio_no_necessita_propera_data(manager):
    mask = inventory.create_item(
        equipment_type=EquipmentType.objects.get(name="Màscara"), by=manager
    )
    review = schedule(mask, manager, kind="visual_inspection")
    reviews.close_review(review, done_on=TODAY, result="ok", by=manager)
    mask.refresh_from_db()
    assert (mask.status, mask.next_review_on) == ("available", None)


@pytest.mark.parametrize(
    "extra",
    [
        {"result": "maybe"},
        {"cost_cents": -1},
        {"cost_cents": 1.5},
        {"next_review_on": None},
        {"next_review_on": TODAY},  # no després de la revisió
        {"done_on": None},
    ],
)
def test_tancament_que_no_val(manager, extra):
    review = schedule(tank(manager), manager)
    fields = {"done_on": TODAY, "result": "ok", "next_review_on": datetime.date(2028, 6, 1)}
    with pytest.raises(ValidationError):
        reviews.close_review(review, by=manager, **{**fields, **extra})
    assert EquipmentReview.objects.get(pk=review.pk).done_on is None


def test_una_sola_revisio_oberta_i_cap_per_a_una_baixa(manager):
    item = tank(manager)
    schedule(item, manager)
    with pytest.raises(ValidationError):
        schedule(item, manager)
    other = tank(manager)
    inventory.change_status(other, "retired", by=manager, reason="Perduda")
    with pytest.raises(ValidationError):
        schedule(other, manager)
    for extra in ({"kind": "pintura"}, {"due_on": None}, {"provider": "x" * 121}):
        with pytest.raises(ValidationError):
            schedule(tank(manager), manager, **extra)


def test_rn_m03_15_peces_que_vencen_i_vencudes(manager):
    soon = tank(manager, review_on=TODAY + datetime.timedelta(days=30))
    later = tank(manager, review_on=TODAY + datetime.timedelta(days=31))
    late = tank(manager, review_on=TODAY - datetime.timedelta(days=1))
    retired = tank(manager, review_on=TODAY - datetime.timedelta(days=5))
    inventory.change_status(retired, "retired", by=manager, reason="Perduda")
    assert list(reviews.due_items(TODAY)) == [late, soon]  # 30 dies (VC-29)
    assert list(reviews.overdue_items(TODAY)) == [late]
    assert later not in reviews.due_items(TODAY)


def test_enviar_una_peca_que_ja_era_en_revisio(manager):
    item = tank(manager)
    inventory.change_status(item, "in_review", by=manager)
    review = schedule(item, manager)
    reviews.send_review(review, sent_on=TODAY, by=manager)
    assert EquipmentItem.objects.get(pk=item.pk).status == "in_review"


def test_sense_mt11_no_es_toca(make_admin, monkeypatch, manager):  # noqa: F811
    item = tank(manager)
    monkeypatch.setattr(access, "allowed", lambda by, code, obj=None: False)
    with pytest.raises(Http404):
        schedule(item, make_admin("secretary"))


def test_la_base_de_dades_vol_resultat_amb_la_data(manager):
    review = schedule(tank(manager), manager)
    with pytest.raises(IntegrityError), transaction.atomic():
        EquipmentReview.objects.filter(pk=review.pk).update(done_on=TODAY)
