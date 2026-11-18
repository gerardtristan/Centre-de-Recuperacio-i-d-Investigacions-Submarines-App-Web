"""Campanya de mandats nous (T-M05a-13; P-M05a-E; RN-M05a-14; CA-M05a-12; escenari B, 022).

- Obrir: amb la signatura del mandat encesa (`MANDATE_SIGNING_ENABLED`), l'identificador de
  creditor (RN-M05a-04) i el text de la invitació publicat (tipus `INVITATION_TEXT`). Una sola
  campanya oberta alhora ([P-211](docs/decisions/pendents.md)).
- Convidar: un correu per soci actiu sense mètode i amb adreça. Tornar-ho a fer només convida
  els que falten. Sense la signatura encesa no surt res (salvaguarda dura: la invitació porta a
  una pàgina que ha de funcionar).
- Recordatoris: a qui no ha triat, als dies des de la invitació de l'ajust VC-11
  (`REMINDER_DAYS`). El darrer, quan el tresorer fixa la remesa (`send_final_reminders`).
- Recompte per resposta, i tancar (P-135, opció per defecte A): tancada, no surt res més.

Cap correu porta dades bancàries; el registre d'activitat només porta recomptes.
"""

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext

from apps.core import audit, business_settings, consents, mail
from apps.members import recipients
from apps.members.models import Member
from apps.members.services import active_members_for_mandates

from .models import FeeMethod, FeePaymentPreference, MandateCampaign, MandateCampaignRecipient

INVITATION_TEXT = "mandate_campaign_invitation"
INVITATION_TEMPLATE = "campanya-mandats-invitacio"
REMINDER_TEMPLATE = "campanya-mandats-recordatori"
FINAL_REMINDER_TEMPLATE = "campanya-mandats-darrer-recordatori"
# VC-11 (RN-M05a-14): dies des de la invitació, de 1 a 60; inicialment 7 i 14 (T-M05a-22).
REMINDER_DAYS = "payments.mandate_campaign_reminder_days"
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


def check_can_send(campaign: MandateCampaign) -> None:
    _require_signing()
    if campaign.closed_at is not None:
        raise Closed


def blocking_reason() -> str | None:
    """Per què no es pot obrir ni enviar cap campanya ara, per a la pantalla; None si es pot."""
    if not settings.MANDATE_SIGNING_ENABLED:
        return gettext("La signatura del mandat no està activada: no es pot obrir ni enviar res.")
    if not settings.SEPA_CREDITOR_IDENTIFIER:
        return gettext("Falta l'identificador de creditor del banc (RN-M05a-04).")
    if consents.current_text(INVITATION_TEXT) is None:
        return gettext("Falta publicar el text de la invitació (T-M05a-01).")
    return None


def to_invite(campaign: MandateCampaign | None) -> list[tuple]:
    """Socis actius sense mètode que encara no s'han convidat, amb l'adreça ("" si no en
    tenen: no es conviden i els atén la secretaria, P-199)."""
    members = _without_method(_active_members()).select_related("person")
    if campaign is not None:
        members = members.exclude(pk__in=campaign.recipients.values("member"))
    return [(member, recipients.email_for(member.person)) for member in members]


def send_invitations(campaign: MandateCampaign, *, by) -> int:
    """CA-M05a-12: només els socis actius sense mètode. Torna quants n'ha convidat."""
    check_can_send(campaign)
    sent = 0
    for member, address in to_invite(campaign):
        if not address:
            continue
        with transaction.atomic():
            MandateCampaignRecipient.objects.create(
                campaign=campaign, member=member, invited_at=timezone.now()
            )
            context = {"text": campaign.invitation_text.content, "link": _link()}
            mail.queue_email(INVITATION_TEMPLATE, to=address, person=member.person, context=context)
        sent += 1
    audit.record(
        "payments.campaign.invitations_sent",
        actor=by,
        target=campaign,
        details={"sent": sent, "text_version": campaign.invitation_text.version},
    )
    return sent


def reminder_days(today=None) -> list[int]:
    """Els dies de VC-11 vigents (per defecte, avui)."""
    return business_settings.get(REMINDER_DAYS, today or timezone.localdate())


def _reminders_due(recipient: MandateCampaignRecipient, today, days: list[int]) -> int:
    """Quants recordatoris tocarien avui des de la invitació."""
    invited_on = timezone.localdate(recipient.invited_at)
    return sum(invited_on + timedelta(days=n) <= today for n in days)


def send_due_reminders(today=None) -> int:
    """Cada dia: un recordatori a qui encara no ha triat i en té un que toca. Si se n'ha
    saltat algun (la tasca no ha corregut), només n'envia un (P-210). Torna quants n'ha enviat."""
    if not settings.MANDATE_SIGNING_ENABLED:
        return 0
    today = today or timezone.localdate()
    days = reminder_days(today)
    pending = MandateCampaignRecipient.objects.filter(
        campaign__closed_at__isnull=True,
        answered_at__isnull=True,
        final_reminder_at__isnull=True,
        reminders_sent__lt=len(days),
        member__in=_without_method(_active_members()),
    ).select_related("member__person")
    sent = 0
    for recipient in pending:
        due = _reminders_due(recipient, today, days)
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


@transaction.atomic
def send_final_reminders(collection_date, *, by) -> int:
    """RN-M05a-14 i 18: el darrer recordatori, quan el tresorer fixa la remesa
    (`remittances.build_remittance`), a qui de la campanya oberta encara no ha triat. Un sol cop
    per soci i campanya, encara que es facin més remeses; després ja no en surt cap altre. Torna
    quants n'ha enviat."""
    if not settings.MANDATE_SIGNING_ENABLED:
        return 0
    pending = list(
        MandateCampaignRecipient.objects.select_for_update(of=("self",))
        .filter(
            campaign__closed_at__isnull=True,
            answered_at__isnull=True,
            final_reminder_at__isnull=True,
            member__in=_without_method(_active_members()),
        )
        .select_related("member__person")
    )
    sent, now = 0, timezone.now()
    for recipient in pending:
        recipient.final_reminder_at = now
        recipient.save(update_fields=["final_reminder_at"])
        address = recipients.email_for(recipient.member.person)
        if address:
            context = {"link": _link(), "collection_date": collection_date}
            mail.queue_email(
                FINAL_REMINDER_TEMPLATE, to=address, person=recipient.member.person, context=context
            )
            sent += 1
    if pending:
        details = {"sent": sent, "collection_date": collection_date.isoformat()}
        audit.record("payments.campaign.final_reminders_sent", actor=by, details=details)
    return sent


def record_answer(member, method: str) -> None:
    """La primera resposta del soci a la campanya oberta (la crida `set_preference`)."""
    MandateCampaignRecipient.objects.filter(
        member=member, campaign__closed_at__isnull=True, answered_at__isnull=True
    ).update(answer=method, answered_at=timezone.now())


def campaign_status(campaign: MandateCampaign | None) -> dict:
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
        "invited": campaign.recipients.count() if campaign else 0,
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
