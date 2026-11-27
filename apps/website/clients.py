"""Excepció de client de l'art. 21.2 LSSI (T-M07-36; decisió 108, C.3; P-710, resposta pendent de
la gestoria).

Qui paga una quota, una inscripció a una activitat o a un curs, o una llicència (l'esdeveniment
`charge.paid` de la 00, que ja escolten el 02 i el 06) rep per defecte el butlletí del club, amb la
baixa a cada correu. **Irreversible (D2):** tot és darrere de `website.client_exception_enabled`,
**apagat**: apagat, el subscriptor no dona d'alta ningú i `newsletter.recipients` no envia res a
cap alta d'aquesta base (tampoc a les que es van fer mentre era encès).

- Mai es dona d'alta qui ja hi té una subscripció (pendent, confirmada o de baixa) ni qui ha dit
  que no (`ClientObjection`): la casella «No vull rebre informació d'activitats» en donar les dades
  (`object_to`, que han de cridar els formularis del 01, el 02 i el 06) o qualsevol baixa.
- El correu és el de contacte de la persona del càrrec i, si no en té, el d'entrada del seu compte
  personal. Una persona anonimitzada, mai.
"""

import hashlib
import hmac
import secrets

from django import forms
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy

from apps.core import audit, business_settings
from apps.core.persons import ANONYMOUS_EMAIL_DOMAIN

from .models import ClientObjection, NewsletterEvent, NewsletterSubscription

SWITCH = "website.client_exception_enabled"
KINDS = frozenset(
    {"fee", "enrolment", "licence"}
)  # `core.Charge.Kind`: quota, inscripció, llicència
ADDED = "website.client_exception_added"
ACTOR = audit.system("website.client_exception")


def enabled() -> bool:
    return bool(business_settings.get(SWITCH))


def _hash(email: str) -> str:
    key = settings.SECRET_KEY.encode()
    return hmac.new(key, email.strip().lower().encode(), hashlib.sha256).hexdigest()


def object_to(email: str) -> None:
    """La persona diu que no (casella en donar les dades o baixa): no es tornarà a donar d'alta
    per aquesta via. Es desa encara que l'interruptor sigui apagat."""
    if email and email.strip():
        ClientObjection.objects.get_or_create(email_hash=_hash(email))


FIELD = "no_activity_info"


def objection_field() -> forms.BooleanField:
    """La casella per dir que no en donar les dades (T-M07-36), igual a tots els formularis del 02
    i del 06. Surt sempre, també amb l'interruptor apagat, perquè el «no» valgui quan s'encengui."""
    return forms.BooleanField(
        label=gettext_lazy("No vull rebre informació d'activitats del C.R.I.S."), required=False,
        help_text=gettext_lazy("Marca-la si no vols que el club t'enviï informació de les seves "
                               "activitats. Cada correu porta l'enllaç per donar-te'n de baixa."),
    )  # fmt: skip


def object_to_person(person) -> None:
    """Com `object_to`, amb el correu que faria servir l'alta (`_email`)."""
    object_to(_email(person))


def objected(email: str) -> bool:
    return ClientObjection.objects.filter(email_hash=_hash(email)).exists()


def _email(person) -> str:
    from apps.accounts.models import Account

    email = person.contact_email
    if not email:
        account = person.accounts.filter(kind=Account.Kind.PERSONAL).first()
        email = account.login if account is not None else ""
    return email.strip().lower()


@transaction.atomic
def on_charge_paid(event) -> NewsletterSubscription | None:
    """Subscriptor de `charge.paid` (es registra a `apps.py`). Apagat, no fa res."""
    if not enabled() or event.payload.get("kind") not in KINDS:
        return None
    from apps.core.models import Charge

    charge = Charge.objects.select_related("person").filter(pk=event.payload.get("charge")).first()
    if charge is None or charge.person.status != charge.person.Status.ACTIVE:
        return None
    email = _email(charge.person)
    if not email or email.endswith("@" + ANONYMOUS_EMAIL_DOMAIN) or objected(email):
        return None
    if NewsletterSubscription.objects.select_for_update().filter(email=email).exists():
        return None
    now = timezone.now()
    subscription = NewsletterSubscription.objects.create(
        email=email, status=NewsletterSubscription.Status.CONFIRMED,
        basis=NewsletterSubscription.Basis.CLIENT, token=secrets.token_urlsafe(32),
        requested_at=now, confirmed_at=now,
    )  # fmt: skip
    NewsletterEvent.objects.create(subscription=subscription, kind=NewsletterEvent.Kind.CLIENT)
    audit.record(ADDED, actor=ACTOR, target=subscription, details={"charge": charge.pk})
    return subscription
