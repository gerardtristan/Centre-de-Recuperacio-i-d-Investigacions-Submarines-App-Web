"""Revisions del material: registre, enviament, tancament i peces que vencen (T-M03-14;
RN-M03-15; CA-M03-11 i 12). Tot amb MT11. L'avís diari per correu (`send_due_notices`) el crida la
tasca de la cua `equipment.review_notices`; l'avís a l'app espera un lloc on posar-lo."""

import datetime

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from apps.core import audit, business_settings, mail
from apps.core.permissions import accounts_with_perm

from .access import REVIEWS, require
from .inventory import S, _set_status
from .models import EquipmentItem, EquipmentReview

NOTICE_DAYS = "equipment.review_notice_days"  # VC-29
REVIEW_SCHEDULED = "equipment.review_scheduled"
REVIEW_SENT = "equipment.review_sent"
REVIEW_CLOSED = "equipment.review_closed"
NOTICE_TEMPLATE = "avis-revisio-material"


def _date(value, label):
    if not isinstance(value, datetime.date):
        raise ValidationError(_("Cal %(field)s.") % {"field": label})
    return value


@transaction.atomic
def schedule_review(item, *, kind, due_on, by, provider="", notes="") -> EquipmentReview:
    """Una revisió prevista d'una peça que no és de baixa; com a màxim una d'oberta per peça."""
    require(by, REVIEWS)
    item = EquipmentItem.objects.select_for_update().get(pk=item.pk)
    if item.status == S.RETIRED:
        raise ValidationError(_("Una peça donada de baixa no es revisa."))
    if kind not in EquipmentReview.Kind.values:
        raise ValidationError(_("Tria el tipus de revisió."))
    provider = (provider or "").strip()
    if len(provider) > 120:
        raise ValidationError(_("Qui la fa té 120 caràcters com a màxim."))
    try:
        with transaction.atomic():
            review = EquipmentReview.objects.create(
                item=item,
                kind=kind,
                due_on=_date(due_on, _("la data prevista")),
                provider=provider,
                notes=(notes or "").strip(),
                recorded_by=by,
            )
    except IntegrityError as error:
        raise ValidationError(_("Aquesta peça ja té una revisió oberta.")) from error
    audit.record(REVIEW_SCHEDULED, actor=by, target=review, details={"item": item.code})
    return review


def _open(review, by) -> EquipmentReview:
    require(by, REVIEWS)
    review = EquipmentReview.objects.select_for_update().select_related("item").get(pk=review.pk)
    if review.done_on is not None:
        raise ValidationError(_("Una revisió tancada no es modifica."))
    return review


@transaction.atomic
def send_review(review, *, sent_on, by) -> EquipmentReview:
    """La peça surt a revisar: passa a «en revisió» (RN-M03-04) i no es pot assignar."""
    review = _open(review, by)
    review.sent_on = _date(sent_on, _("la data d'enviament"))
    review.save()
    item = EquipmentItem.objects.select_for_update().get(pk=review.item_id)
    if item.status == S.AVAILABLE:
        _set_status(item, S.IN_REVIEW, by=by)
    audit.record(REVIEW_SENT, actor=by, target=review, details={"sent_on": sent_on.isoformat()})
    return review


@transaction.atomic
def close_review(
    review, *, done_on, result, by, cost_cents=None, next_review_on=None, notes=""
) -> EquipmentReview:
    """Correcta: la peça torna a estar disponible amb la propera revisió. Fallida: la peça es dona
    de baixa amb el motiu (CA-M03-12). Les assignacions futures es marcaran amb la T-M03-08."""
    review = _open(review, by)
    if result not in EquipmentReview.Result.values:
        raise ValidationError(_("El resultat és «correcta» o «fallida»."))
    if cost_cents is not None and (
        isinstance(cost_cents, bool) or not isinstance(cost_cents, int) or cost_cents < 0
    ):
        raise ValidationError(_("El cost és un enter de cèntims, zero o més."))
    item = EquipmentItem.objects.select_for_update().select_related("type").get(pk=review.item_id)
    done_on = _date(done_on, _("la data de la revisió"))
    if result == EquipmentReview.Result.OK and item.type.requires_review:
        if _date(next_review_on, _("la data de la propera revisió")) <= done_on:
            raise ValidationError(_("La propera revisió ha de ser després d'aquesta."))
    review.done_on, review.result, review.cost_cents = done_on, result, cost_cents
    review.next_review_on = next_review_on
    review.notes = "\n".join(filter(None, [review.notes, (notes or "").strip()]))
    review.save()
    if result == EquipmentReview.Result.OK:
        if next_review_on is not None:
            item.next_review_on = next_review_on
            item.save(update_fields=["next_review_on"])
        if item.status == S.IN_REVIEW:
            _set_status(item, S.AVAILABLE, by=by)
    else:
        reason = gettext("Revisió fallida (%(kind)s) del %(date)s") % {
            "kind": review.get_kind_display(),
            "date": done_on.strftime("%d/%m/%Y"),
        }
        _set_status(item, S.RETIRED, by=by, reason=reason)
    audit.record(
        REVIEW_CLOSED,
        actor=by,
        target=review,
        details={"result": result, "cost_cents": cost_cents, "item": item.code},
    )
    return review


def due_items(today):
    """RN-M03-15: les peces que no són de baixa amb la revisió dins els dies de l'ajust
    `equipment.review_notice_days` o ja vençuda, per data. L'avís diari les farà servir."""
    days = business_settings.get(NOTICE_DAYS, today)
    return (
        EquipmentItem.objects.exclude(status=S.RETIRED)
        .filter(next_review_on__lte=today + datetime.timedelta(days=days))
        .order_by("next_review_on", "code")
    )


def send_due_notices(today=None) -> int:
    """CA-M03-11: un correu a cada compte amb MT11 (i correu de notificació) amb les peces que
    vencen o han vençut. Sense peces, cap correu. Només codis i tipus: cap dada personal."""
    today = today or timezone.localdate()
    items = [
        {"code": i.code, "type": i.type.name, "next_review_on": i.next_review_on,
         "overdue": i.next_review_on < today}
        for i in due_items(today).select_related("type")
    ]  # fmt: skip
    if not items:
        return 0
    sent = 0
    for account in accounts_with_perm(REVIEWS, write=True):
        if account.notification_email:
            mail.queue_email(
                NOTICE_TEMPLATE, to=account.notification_email, person=account.person,
                context={"items": items},
            )  # fmt: skip
            sent += 1
    return sent


def overdue_items(today):
    return due_items(today).filter(next_review_on__lt=today)


def reviews_with_cost(starts_on, ends_on):
    """`equipment.reviews_with_cost` (M03-8): revisions tancades amb cost dins un període, per
    casar-les amb les factures (09)."""
    return EquipmentReview.objects.filter(
        done_on__range=(starts_on, ends_on), cost_cents__isnull=False
    ).select_related("item")
