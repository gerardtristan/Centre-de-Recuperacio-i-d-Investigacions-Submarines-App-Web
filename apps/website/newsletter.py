"""Butlletí: subscripció amb doble confirmació, consentiment i baixa (T-M07-13; P-M07-E;
RN-M07-06 i 08; CA-M07-06, 07, 09 i 10). Tot darrere de `website.newsletter_enabled` (apagat;
no s'encén a producció sense la P-42).

- `subscribe`: la mateixa resposta per a tothom (ho fa la vista). Un correu ja confirmat no canvia
  ni rep res; un de nou, un de pendent o un de baixa queda pendent amb un enllaç nou.
- `confirm`: d'un sol ús en efecte (obrir-lo dues vegades deixa una sola subscripció confirmada);
  passades `website.newsletter_confirm_hours`, no subscriu.
- `unsubscribe`: immediata, sense sessió, i tornar-la a obrir no canvia res. En queda només la
  traça (M07-12, T-M07-15): el correu se substitueix (`forget`).

Falta (torn del nucli): enviar el correu de confirmació; la plantilla es declara a
`core.mail.TEMPLATE_PRIORITIES`. Vegeu `docs/estat/M07.md`.
"""

import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.core import business_settings
from apps.core.persons import ANONYMOUS_EMAIL_DOMAIN

from .models import NewsletterEvent, NewsletterSubscription

ENABLED = "website.newsletter_enabled"
CONFIRM_HOURS = "website.newsletter_confirm_hours"
TEXT_KIND = "newsletter"
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
    subscription = subscription or NewsletterSubscription(email=normalise(email))
    subscription.status, subscription.legal_text = Status.PENDING, legal_text
    subscription.token, subscription.requested_at = secrets.token_urlsafe(32), now
    subscription.save()
    NewsletterEvent.objects.create(subscription=subscription, kind=Kind.REQUESTED)
    return subscription, True


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
