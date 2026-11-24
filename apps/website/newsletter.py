"""Butlletí: subscripció amb doble confirmació, consentiment i baixa (T-M07-13; P-M07-E;
RN-M07-06 i 08; CA-M07-06, 07, 09 i 10). Tot darrere de `website.newsletter_enabled` (apagat;
no s'encén a producció sense la P-42).

- `subscribe`: la mateixa resposta per a tothom (ho fa la vista). Un correu ja confirmat no canvia
  ni rep res; un de pendent amb l'enllaç vigent el conserva, i amb l'enllaç caducat en rep un de
  nou; un de nou (també el d'una baixa anterior, que ja no guarda el correu: `forget`) és una fila
  nova pendent.
- `confirm`: d'un sol ús en efecte (obrir-lo dues vegades deixa una sola subscripció confirmada);
  passades `website.newsletter_confirm_hours`, no subscriu.
- `unsubscribe`: immediata, sense sessió, i tornar-la a obrir no canvia res. En queda només la
  traça (M07-12, T-M07-15): el correu se substitueix (`forget`).
- `send_confirmation`: el correu de confirmació (T-M07-13b), sempre a la cua, amb l'enllaç i
  res més; la vista hi aplica abans el límit per destinatari.
"""

import secrets
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit, business_settings, mail
from apps.core.models import OutgoingEmail
from apps.core.permissions import has_perm
from apps.core.persons import ANONYMOUS_EMAIL_DOMAIN

from .models import Newsletter, NewsletterDelivery, NewsletterEvent, NewsletterSubscription

ENABLED = "website.newsletter_enabled"
CONFIRM_HOURS = "website.newsletter_confirm_hours"
TEXT_KIND = "newsletter"
CONFIRMATION_TEMPLATE = "confirmacio-butlleti"
Status = NewsletterSubscription.Status
Kind = NewsletterEvent.Kind


def normalise(email: str) -> str:
    return email.strip().lower()


@transaction.atomic
def subscribe(email: str, *, legal_text, now=None) -> tuple[NewsletterSubscription, bool]:
    """Torna la subscripció i si cal enviar-li la confirmació (CA-M07-06)."""
    now = now or timezone.now()
    subscription = (
        NewsletterSubscription.objects.select_for_update().filter(email=normalise(email)).first()
    )
    # El correu de confirmació (T-M07-13b) va sempre a la cua (`mail.queue_email`), mai en línia:
    # el temps de resposta no ha de dir si el correu ja hi era (RN-M07-08).
    if subscription is not None and subscription.status == Status.CONFIRMED:
        return subscription, False
    # Una petició nova no invalida l'enllaç pendent que encara val: si no, un tercer el podria
    # anul·lar a cada petició encara que el límit per destinatari no deixi enviar-ne cap altre.
    keep = (
        subscription is not None
        and subscription.status == Status.PENDING
        and now <= subscription.requested_at + timedelta(hours=business_settings.get(CONFIRM_HOURS))
    )
    subscription = subscription or NewsletterSubscription(email=normalise(email))
    subscription.status, subscription.legal_text = Status.PENDING, legal_text
    if not keep:
        subscription.token, subscription.requested_at = secrets.token_urlsafe(32), now
    subscription.save()
    NewsletterEvent.objects.create(subscription=subscription, kind=Kind.REQUESTED)
    return subscription, True


def send_confirmation(subscription: NewsletterSubscription) -> None:
    """Posa a la cua el correu de confirmació: només l'enllaç (amb el testimoni) i la caducitat."""
    link = settings.PUBLIC_SITE_URL + reverse(
        "website:newsletter_confirm", args=[subscription.token]
    )
    hours = business_settings.get(CONFIRM_HOURS)
    mail.queue_email(
        CONFIRMATION_TEMPLATE, to=subscription.email, context={"link": link, "hours": hours}
    )


def _by_token(token: str):
    return NewsletterSubscription.objects.select_for_update().filter(token=token).first()


@transaction.atomic
def confirm(token: str, *, now=None) -> NewsletterSubscription | None:
    """La subscripció confirmada, o `None` si l'enllaç no val (no existeix, ha caducat o és d'una
    baixa)."""
    now = now or timezone.now()
    subscription = _by_token(token)
    if subscription is None or subscription.status == Status.UNSUBSCRIBED:
        return None
    if subscription.status == Status.CONFIRMED:
        return subscription
    hours = business_settings.get(CONFIRM_HOURS)
    if now > subscription.requested_at + timedelta(hours=hours):
        return None
    subscription.status, subscription.confirmed_at = Status.CONFIRMED, now
    subscription.save(update_fields=["status", "confirmed_at"])
    NewsletterEvent.objects.create(
        subscription=subscription, kind=Kind.CONFIRMED, legal_text=subscription.legal_text
    )
    return subscription


@transaction.atomic
def unsubscribe(token: str, *, now=None) -> None:
    """Immediata; sense resposta diferent si l'enllaç no existeix (RN-M07-08)."""
    subscription = _by_token(token)
    if subscription is not None:
        forget(subscription, now=now)


def forget(subscription: NewsletterSubscription, *, now=None) -> None:
    """La baixa, de la persona o de l'esborrat RGPD (T-M07-15): en queda només la traça (M07-12):
    l'estat, la versió del text, les dates i els esdeveniments; el correu se substitueix."""
    if subscription.status != Status.UNSUBSCRIBED:
        subscription.status = Status.UNSUBSCRIBED
        subscription.unsubscribed_at = now or timezone.now()
        NewsletterEvent.objects.create(subscription=subscription, kind=Kind.UNSUBSCRIBED)
    subscription.email = f"baixa-{subscription.pk}@{ANONYMOUS_EMAIL_DOMAIN}"
    subscription.save(update_fields=["status", "unsubscribed_at", "email"])


def recipients():
    """Els únics que reben un butlletí (RN-M07-06): els confirmats."""
    return NewsletterSubscription.objects.filter(status=Status.CONFIRMED)


# --- Redactar i enviar (T-M07-14; P-M07-F, RN-M07-06 i 14; CA-M07-08) --------------------------
# WP6 al servei; WP6 veu el nombre de destinataris i els recomptes, mai cap correu (WP7). Tot
# darrere de `website.newsletter_enabled`: apagat, «no trobat».

PERMISSION = "website.newsletter"  # WP6
TEMPLATE = "butlleti"  # `core.mail.TEMPLATE_PRIORITIES`, prioritat de butlletí (T-M07-14b)
ACTION_SENT = "website.newsletter_sent"
# Tècnic, no de negoci: quants correus posa a la cua cada tasca. La cua i el límit diari (T-M00-06)
# decideixen quan surten.
BATCH_SIZE = 50


def _require(actor):
    if not business_settings.get(ENABLED) or not has_perm(actor, PERMISSION, write=True):
        raise Http404


def save_draft(*, actor, subject: str, body: str, newsletter: Newsletter | None = None):
    """Crea o canvia un esborrany. Un butlletí enviat no es canvia."""
    _require(actor)
    if newsletter is None:
        last = Newsletter.objects.aggregate(last=Max("number"))["last"] or 0
        newsletter = Newsletter(number=last + 1, created_by=actor)
    elif newsletter.status != Newsletter.Status.DRAFT:
        raise ValidationError(_("Un butlletí enviat no es pot canviar."))
    newsletter.subject, newsletter.body = subject.strip(), body.strip()
    newsletter.full_clean(exclude=["created_by"])
    newsletter.save()
    return newsletter


def recipients_count(actor) -> int:
    """El que veu WP6 abans d'enviar: quants, mai qui."""
    _require(actor)
    return recipients().count()


@transaction.atomic
def send(newsletter: Newsletter, *, actor, request=None) -> int:
    """Passa a enviat (una sola vegada), deixa un enviament per a cada subscripció confirmada i
    posa els lots a la cua. Torna quants destinataris té."""
    _require(actor)
    newsletter = Newsletter.objects.select_for_update().get(pk=newsletter.pk)
    if newsletter.status != Newsletter.Status.DRAFT:
        raise ValidationError(_("Aquest butlletí ja s'ha enviat."))
    newsletter.status, newsletter.sent_by = Newsletter.Status.SENT, actor
    newsletter.sent_at = timezone.now()
    newsletter.save(update_fields=["status", "sent_by", "sent_at"])
    deliveries = NewsletterDelivery.objects.bulk_create(
        NewsletterDelivery(newsletter=newsletter, subscription=s) for s in recipients()
    )
    audit.record(
        ACTION_SENT, actor=actor, target=newsletter, field="status",
        old=Newsletter.Status.DRAFT, new=newsletter.status,
        details={"recipients": len(deliveries)}, request=request,
    )  # fmt: skip
    from .tasks import send_newsletter_batch

    ids = [d.pk for d in deliveries]
    for start in range(0, len(ids), BATCH_SIZE):
        send_newsletter_batch.defer(delivery_ids=ids[start : start + BATCH_SIZE])
    return len(deliveries)


def send_batch(delivery_ids: list[int]) -> None:
    """Un lot: un correu per enviament, amb l'enllaç de baixa. Idempotent: un enviament que ja té
    correu o que s'ha saltat no es torna a fer."""
    pending = NewsletterDelivery.objects.filter(
        pk__in=delivery_ids, email__isnull=True, skipped=False
    ).select_related("newsletter", "subscription")
    for delivery in pending:
        with transaction.atomic():
            subscription = delivery.subscription
            if subscription.status != Status.CONFIRMED:
                delivery.skipped = True
                delivery.save(update_fields=["skipped"])
                continue
            link = reverse("website:newsletter_unsubscribe", args=[subscription.token])
            delivery.email = mail.queue_email(
                TEMPLATE,
                to=subscription.email,
                context={
                    "subject": delivery.newsletter.subject,
                    "body": delivery.newsletter.body,
                    "unsubscribe_url": settings.PUBLIC_SITE_URL + link,
                },
            )
            delivery.save(update_fields=["email"])


def counts(newsletter: Newsletter, *, actor) -> dict:
    """CA-M07-08: enviats, fallits i baixes posteriors; només recomptes (WP6)."""
    _require(actor)
    deliveries = newsletter.deliveries
    # De la base de dades: la instància de qui crida pot ser d'abans d'enviar-lo.
    sent_at = Newsletter.objects.values_list("sent_at", flat=True).get(pk=newsletter.pk)
    unsubscribed = (
        NewsletterEvent.objects.filter(
            subscription__deliveries__newsletter=newsletter, kind=Kind.UNSUBSCRIBED, at__gte=sent_at
        )
        if sent_at
        else NewsletterEvent.objects.none()
    )
    return {
        "recipients": deliveries.count(),
        "sent": deliveries.filter(email__status=OutgoingEmail.Status.SENT).count(),
        "failed": deliveries.filter(email__status=OutgoingEmail.Status.FAILED).count(),
        "unsubscribed_after": unsubscribed.count(),
    }
