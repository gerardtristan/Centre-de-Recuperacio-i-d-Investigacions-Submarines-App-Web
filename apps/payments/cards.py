"""Targeta guardada per a les quotes (T-M05a-12; P-M05a-D; RN-M05a-10; CA-M05a-15). Condicional a
la P-45, punt 6: es construeix contra el proveïdor fals, que declara que la sap guardar (092).

- La targeta s'escriu i s'autentica a la pàgina del proveïdor: aquí només arriben la referència
  del proveïdor, els quatre darrers dígits i la caducitat (CA-M05a-15).
- Es dona per guardada amb la notificació verificada (`processing`) o amb la consulta de la
  xarxa de seguretat, mai amb la tornada del navegador; la targeta es consulta al proveïdor,
  servidor a servidor.
- Guardar-la no cobra res: no passa per la salvaguarda del nivell 1 (és recollir el mètode).
- Una persona té com a molt una targeta activa: la nova deixa l'anterior «esborrada» (P-297), i
  la preferència de la quota passa a «targeta guardada» amb la nova (P-298; com la P-125 amb el
  mandat, 095).
- La referència del proveïdor no surt a cap pantalla, registre d'activitat ni correu.
"""

from django.conf import settings
from django.db import transaction
from django.http import Http404
from django.urls import reverse

from apps.core import audit
from apps.core.models import Person
from apps.members.models import Member

from . import preferences
from .models import CardSetup, FeeMethod, ProviderEvent, SavedCard
from .providers import base, get_provider

STARTED = "payments.card_setup.started"
SAVED = "payments.saved_card.saved"
REPLACED = "payments.saved_card.replaced"
REMOVED = "payments.saved_card.removed"
FAILED = "payments.card_setup.failed"
ACTOR = audit.system("payments.cards")
CURRENCY = "EUR"  # la de l'autorització de 0 €: la dels càrrecs del club (`Charge.currency`)
KNOWN = (base.PAID, base.DENIED, base.EXPIRED)
IN_PROGRESS = CardSetup.Status.IN_PROGRESS


def start_setup(member, account) -> str:
    """Obre l'autenticació al proveïdor i torna l'adreça on el soci escriu la targeta. La vista
    ja ha comprovat el soci de la sessió i la sessió recent (RN-M05a-12). Les autenticacions
    anteriors de la persona que encara eren obertes es tanquen: una que acabi tard no guarda
    res i va «a revisar»."""
    provider = get_provider()
    site = settings.PUBLIC_SITE_URL
    back = site + reverse("payments:saved_card") + "?tornada={}"
    urls = base.OrderUrls(
        notification=site + reverse("payments:provider_notification", args=[provider.code]),
        return_ok=back.format("ok"),
        return_ko=back.format("ko"),
    )
    order = provider.start_card_setup(member.person, urls)
    with transaction.atomic():
        earlier = CardSetup.objects.select_for_update().filter(
            person=member.person, status=IN_PROGRESS
        )
        for old in earlier:
            _fail(old, "replaced")
        setup = CardSetup.objects.create(
            person=member.person,
            started_by=account,
            provider_code=provider.code,
            provider_order_id=order.external_id,
        )
        audit.record(STARTED, actor=account, target=setup)
    return order.pay_url


def setup_for(event: ProviderEvent) -> CardSetup | None:
    orders = CardSetup.objects.filter(provider_code=event.provider_code)
    return orders.filter(provider_order_id=event.order_id).exclude(provider_order_id="").first()


def _fail(setup: CardSetup, status: str) -> None:
    setup.status = CardSetup.Status.FAILED
    setup.save(update_fields=["status", "updated_at"])
    audit.record(FAILED, actor=ACTOR, target=setup, details={"status": status})


def settle_setup(setup: CardSetup, state: base.OrderState) -> str | None:
    """Aplica a l'autenticació l'estat de la seva ordre al proveïdor, vingui d'una notificació
    verificada o de la xarxa de seguretat. Dins d'una transacció. Torna el motiu si va «a
    revisar». Una autenticació ja tancada no canvia (idempotent)."""
    setup = CardSetup.objects.select_for_update().get(pk=setup.pk)
    if state.status == base.PENDING:
        return None
    if state.status not in KNOWN:
        return "El proveïdor torna un estat desconegut de l'autenticació de la targeta."
    if (state.amount_cents, state.currency) != (0, CURRENCY):
        return "L'autenticació de la targeta porta un import o una moneda inesperats."
    if setup.status != IN_PROGRESS:
        if setup.status == CardSetup.Status.FAILED and state.status == base.PAID:
            return "Targeta autenticada d'una autenticació ja tancada: no s'ha guardat."
        return None
    if state.status != base.PAID:
        _fail(setup, state.status)
        return None
    card = get_provider().get_card_setup(setup.provider_order_id)
    # Una sola targeta activa per persona (P-297, també amb un índex únic): dues alhora, en fila.
    Person.objects.select_for_update().get(pk=setup.person_id)
    for old in SavedCard.objects.filter(person=setup.person, status=SavedCard.Status.ACTIVE):
        old.status = SavedCard.Status.REMOVED
        old.save(update_fields=["status"])
        audit.record(REPLACED, actor=ACTOR, target=old, field="status", old="active", new="removed")
    # Les restriccions del model rebutgen uns dígits o un mes que no ho són: tot es desfà, la
    # notificació queda en «error» i la xarxa de seguretat ho torna a provar.
    saved = SavedCard(
        person=setup.person,
        provider_code=setup.provider_code,
        provider_card_id=card.card_ref,
        last4=card.last4,
        expiry_month=card.expiry_month,
        expiry_year=card.expiry_year,
    )
    saved.full_clean()
    saved.save()
    setup.status, setup.saved_card = CardSetup.Status.SAVED, saved
    setup.save(update_fields=["status", "saved_card", "updated_at"])
    details = {"last4": saved.last4, "expiry": f"{saved.expiry_month}/{saved.expiry_year}"}
    audit.record(SAVED, actor=ACTOR, target=saved, details=details)
    member = Member.objects.filter(
        person=setup.person,
        status__in=[Member.Status.ACTIVE, Member.Status.UNPAID],
        member_number__isnull=False,
    ).first()
    if member is not None:
        try:
            with transaction.atomic():
                preferences.set_preference(member, FeeMethod.SAVED_CARD, by=setup.started_by)
        except preferences.PreferenceError:
            return "La targeta s'ha guardat, però no s'ha pogut canviar com es paga la quota."
    return None


def stale_setups(provider_code: str, before):
    """Les autenticacions encara obertes, començades abans de `before` (xarxa de seguretat)."""
    setups = CardSetup.objects.filter(
        status=IN_PROGRESS, provider_code=provider_code, created_at__lt=before
    )
    return setups.exclude(provider_order_id="").order_by("pk")


def give_up(setup: CardSetup, before) -> None:
    """Una autenticació que el proveïdor no ha tancat passades les hores de la xarxa de seguretat
    (VC-17) es dona per abandonada: no es guarda cap targeta."""
    with transaction.atomic():
        setup = CardSetup.objects.select_for_update().get(pk=setup.pk)
        if setup.status == IN_PROGRESS and setup.created_at < before:
            _fail(setup, "abandoned")


def waiting(person) -> bool:
    """Hi ha una autenticació començada que el proveïdor encara no ha confirmat."""
    return CardSetup.objects.filter(person=person, status=IN_PROGRESS).exists()


@transaction.atomic
def remove_card(member, *, by) -> SavedCard | None:
    """El soci esborra la seva targeta guardada (P-132, opció A: com revocar el mandat). Només
    des del seu compte personal; la vista ja ha demanat la confirmació i la sessió recent
    (RN-M05a-12). Passa a «esborrada», no es cobra mai més, i la preferència, si era la targeta
    (o no n'hi havia), passa a «pagar cada vegada». Funciona encara que el proveïdor ja no guardi
    targetes. Torna la targeta, o None si no n'hi havia cap d'activa.

    shortcut: no es demana al proveïdor que l'esborri (l'adaptador no ho sap fer); a la
    plataforma ja no es pot fer servir. Amb el proveïdor real (P-45, punt 6), P-402."""
    from .mandates import _is_own  # mandates → processing → cards: import circular a dalt

    if not _is_own(by, member):
        raise Http404
    card = (
        SavedCard.objects.select_for_update()
        .filter(person=member.person, status=SavedCard.Status.ACTIVE)
        .first()
    )
    if card is None:
        return None
    card.status = SavedCard.Status.REMOVED
    card.save(update_fields=["status"])
    audit.record(REMOVED, actor=by, target=card)
    preference = preferences.current(member)
    if preference is None or preference.method == FeeMethod.SAVED_CARD:
        preferences.set_preference(member, FeeMethod.PAY_EACH_TIME, by=by)
    return card
