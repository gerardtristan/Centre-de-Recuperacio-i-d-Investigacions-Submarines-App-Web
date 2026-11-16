"""Campanya de mandats nous (T-M05a-13; P-M05a-E; RN-M05a-14; CA-M05a-12; escenari B, 022).

- Obrir: amb la signatura del mandat encesa (`MANDATE_SIGNING_ENABLED`), l'identificador de
  creditor (RN-M05a-04) i el text de la invitació publicat (tipus `INVITATION_TEXT`). Una sola
  campanya oberta alhora ([P-211](docs/decisions/pendents.md)).
- Convidar: un correu per soci actiu sense mètode i amb adreça. Tornar-ho a fer només convida
  els que falten. Sense la signatura encesa no surt res (salvaguarda dura: la invitació porta a
  una pàgina que ha de funcionar).
- Recordatoris: a qui no ha triat, als dies de `REMINDER_DAYS` de la invitació. El darrer
  recordatori, quan el tresorer fixa la remesa, és del 05b.
- Recompte per resposta, i tancar (P-135, opció per defecte A): tancada, no surt res més.

Cap correu porta dades bancàries; el registre d'activitat només porta recomptes.
"""

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from apps.core import audit, consents, mail
from apps.members import recipients
from apps.members.models import Member
from apps.members.services import active_members_for_mandates

from .models import FeeMethod, FeePaymentPreference, MandateCampaign, MandateCampaignRecipient

INVITATION_TEXT = "mandate_campaign_invitation"
INVITATION_TEMPLATE = "campanya-mandats-invitacio"
REMINDER_TEMPLATE = "campanya-mandats-recordatori"
# RN-M05a-14 (7 i 14 dies). VC-11 (`payments.mandate_campaign_reminder_days`) els passa a un
# ajust: ho fa la T-M05a-22, que en llegeix el valor aquí.
REMINDER_DAYS = (7, 14)
ACTOR = audit.system("payments.campaign_reminders")


class CampaignError(Exception):
    pass


class SigningDisabled(CampaignError):
    """La signatura del mandat és apagada: cap campanya ni cap correu."""


class NotReady(CampaignError):
    """Falta l'identificador de creditor o el text de la invitació."""


class AlreadyOpen(CampaignError):
    pass


class Closed(CampaignError):
    pass


def _require_signing() -> None:
    if not settings.MANDATE_SIGNING_ENABLED:
        raise SigningDisabled


def open_campaign(name: str, *, by) -> MandateCampaign:
    _require_signing()
    text = consents.current_text(INVITATION_TEXT)
    if not settings.SEPA_CREDITOR_IDENTIFIER or text is None:
        raise NotReady
    with transaction.atomic():
        # Bloqueja les obertes perquè dues obertures alhora no en deixin dues.
        if list(MandateCampaign.objects.select_for_update().filter(closed_at__isnull=True)):
            raise AlreadyOpen
        campaign = MandateCampaign.objects.create(name=name, opened_by=by, invitation_text=text)
        audit.record("payments.campaign.opened", actor=by, target=campaign)
    return campaign


def open_campaign_now() -> MandateCampaign | None:
    return MandateCampaign.objects.filter(closed_at__isnull=True).first()


def _active_members():
    ids = [summary.person_id for summary in active_members_for_mandates()]
    return Member.objects.filter(person_id__in=ids, status=Member.Status.ACTIVE)


def _without_method(members):
    return members.exclude(pk__in=FeePaymentPreference.objects.values("member"))


def _link() -> str:
    return settings.PUBLIC_SITE_URL + reverse("payments:fee_method")


def _check_open(campaign: MandateCampaign) -> None:
    _require_signing()
    if campaign.closed_at is not None:
        raise Closed


def send_invitations(campaign: MandateCampaign, *, by) -> int:
    """CA-M05a-12: només els socis actius sense mètode. Torna quants n'ha convidat."""
    _check_open(campaign)
    invited = MandateCampaignRecipient.objects.filter(campaign=campaign).values("member")
    sent = 0
    for member in (
        _without_method(_active_members()).exclude(pk__in=invited).select_related("person")
    ):
        address = recipients.email_for(member.person)
        if not address:
            continue  # sense correu: surt al recompte i l'atén la secretaria (P-199)
        with transaction.atomic():
            MandateCampaignRecipient.objects.create(
                campaign=campaign, member=member, invited_at=timezone.now()
            )
            context = {"text": campaign.invitation_text.content, "link": _link()}
            mail.queue_email(INVITATION_TEMPLATE, to=address, person=member.person, context=context)
        sent += 1
    audit.record(
        "payments.campaign.invitations_sent", actor=by, target=campaign, details={"sent": sent}
    )
    return sent


def _reminders_due(recipient: MandateCampaignRecipient, today) -> int:
    """Quants recordatoris tocarien avui des de la invitació."""
    invited_on = timezone.localdate(recipient.invited_at)
    return sum(invited_on + timedelta(days=days) <= today for days in REMINDER_DAYS)


def send_due_reminders(today=None) -> int:
    """Cada dia: un recordatori a qui encara no ha triat i en té un que toca. Si se n'ha
    saltat algun (la tasca no ha corregut), només n'envia un (P-210). Torna quants n'ha enviat."""
    if not settings.MANDATE_SIGNING_ENABLED:
        return 0
    today = today or timezone.localdate()
    pending = MandateCampaignRecipient.objects.filter(
        campaign__closed_at__isnull=True,
        answered_at__isnull=True,
        reminders_sent__lt=len(REMINDER_DAYS),
        member__in=_without_method(_active_members()),
    ).select_related("member__person")
    sent = 0
    for recipient in pending:
        due = _reminders_due(recipient, today)
        if due <= recipient.reminders_sent:
            continue
        address = recipients.email_for(recipient.member.person)
        with transaction.atomic():
            recipient.reminders_sent, recipient.last_reminder_at = due, timezone.now()
            recipient.save(update_fields=["reminders_sent", "last_reminder_at"])
            if address:
                mail.queue_email(
                    REMINDER_TEMPLATE,
                    to=address,
                    person=recipient.member.person,
                    context={"link": _link()},
                )
                sent += 1
    if sent:
        audit.record("payments.campaign.reminders_sent", actor=ACTOR, details={"sent": sent})
    return sent


def record_answer(member, method: str) -> None:
    """La primera resposta del soci a la campanya oberta (la crida `set_preference`)."""
    MandateCampaignRecipient.objects.filter(
        member=member, campaign__closed_at__isnull=True, answered_at__isnull=True
    ).update(answer=method, answered_at=timezone.now())


def campaign_status(campaign: MandateCampaign) -> dict:
    """Recompte dels socis actius per resposta (P-M05a-E, pas 5), i quants s'han convidat."""
    active = _active_members()
    methods = FeePaymentPreference.objects.filter(member__in=active).values_list(
        "method", flat=True
    )
    counts = {method: 0 for method in FeeMethod.values}
    for method in methods:
        counts[method] += 1
    total = active.count()
    return {
        **counts,
        "no_answer": total - sum(counts.values()),
        "active": total,
        "invited": campaign.recipients.count(),
    }


def close_campaign(campaign: MandateCampaign, *, by) -> None:
    """P-135, opció per defecte A: el tresorer la tanca; tancada, no surt cap recordatori més."""
    with transaction.atomic():
        updated = MandateCampaign.objects.filter(pk=campaign.pk, closed_at__isnull=True).update(
            closed_at=timezone.now()
        )
        if not updated:
            raise Closed
        audit.record(
            "payments.campaign.closed",
            actor=by,
            target=campaign,
            details=campaign_status(campaign),
        )
    campaign.refresh_from_db()
