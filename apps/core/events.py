"""Esdeveniments entre mòduls (decisió 049; T-M05b-21).

- `emit(name, payload)` escriu l'esdeveniment i la feina de la cua que el lliura **dins la
  transacció de qui crida**: si el canvi es desfà, l'esdeveniment tampoc no existeix.
- Els mòduls s'hi subscriuen (`subscribe("charge.paid", handler)`, des del seu `ready()`); qui
  l'emet no els coneix.
- La cua (`core.deliver_event`) el lliura com a mínim una vegada i amb reintents. Cada lliurament
  fet deixa una fila única per (esdeveniment, subscriptor), a la mateixa transacció que la feina
  del subscriptor: si arriba dues vegades, el segon no fa res.
- Cada emissió i cada lliurament (fet, fallit o repetit) queden al registre d'activitat.

Només els esdeveniments aprovats: `charge.paid` (049). Un altre s'ha d'aprovar abans (049,
conseqüències).
"""

from collections.abc import Callable

from django.db import transaction

from . import audit
from .models import Event, EventDelivery

CHARGE_PAID = "charge.paid"
APPROVED = frozenset({CHARGE_PAID})

EMITTED = "events.emitted"
DELIVERED = "events.delivered"
REPEATED = "events.delivery_repeated"
FAILED = "events.delivery_failed"

ACTOR = audit.system("events")
# Reintents espaiats durant unes hores; després, la feina queda fallida i al registre (P-245).
MAX_ATTEMPTS = 8

_subscribers: dict[str, dict[str, Callable[[Event], None]]] = {}


class DeliveryFailed(Exception):
    """Algun subscriptor ha fallat: la cua torna a provar l'esdeveniment sencer, i els que ja
    s'havien lliurat no es tornen a executar."""


def _check(name: str) -> None:
    if name not in APPROVED:
        raise ValueError(f"Esdeveniment no aprovat: {name}")


def subscribe(name: str, handler: Callable[[Event], None]) -> None:
    """El subscriptor s'identifica pel nom complet de la funció, que és el que queda a la fila
    del lliurament: si es canvia de nom, rep de nou els esdeveniments que encara es lliurin."""
    _check(name)
    _subscribers.setdefault(name, {})[f"{handler.__module__}.{handler.__qualname__}"] = handler


def emit(name: str, payload: dict) -> Event:
    _check(name)
    from .tasks import deliver_event  # `tasks` importa aquest mòdul

    event = Event.objects.create(name=name, payload=payload)
    audit.record(EMITTED, actor=ACTOR, target=event, details={"event": name})
    deliver_event.defer(event_id=event.pk)
    return event


def deliver(event_id: int) -> None:
    """El cos de la feina de la cua. Lliura l'esdeveniment a cada subscriptor; si algun falla,
    acaba amb `DeliveryFailed` perquè la cua ho torni a provar."""
    name = Event.objects.values_list("name", flat=True).get(pk=event_id)
    failed = [
        key
        for key, handler in list(_subscribers.get(name, {}).items())
        if not _deliver_one(event_id, key, handler)
    ]
    if failed:
        raise DeliveryFailed(", ".join(failed))


def _deliver_one(event_id: int, key: str, handler) -> bool:
    try:
        with transaction.atomic():
            # El pany: dos lliuraments alhora del mateix esdeveniment van un darrere l'altre.
            event = Event.objects.select_for_update().get(pk=event_id)
            if EventDelivery.objects.filter(event=event, subscriber=key).exists():
                audit.record(REPEATED, actor=ACTOR, target=event, details={"subscriber": key})
                return True
            handler(event)
            EventDelivery.objects.create(event=event, subscriber=key)
            audit.record(DELIVERED, actor=ACTOR, target=event, details={"subscriber": key})
            return True
    except Exception as error:
        # Només el tipus d'error: el missatge podria portar dades d'una persona.
        details = {"subscriber": key, "error": type(error).__name__}
        audit.record(FAILED, actor=ACTOR, target=Event.objects.get(pk=event_id), details=details)
        return False
