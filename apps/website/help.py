"""Preguntes freqüents amb cercador (T-M07-09; M07b, P-M07-G, RN-M07-12; CA-M07-16).

- `save_topic` i `save_entry`: WP4 (`website.help`, «Sí») al servidor, amb la fila bloquejada;
  publicar, retirar i canviar una pregunta queden al registre amb el valor anterior (RN-M07-14).
- `published_entries(topic)` i `search(text)`: el que veu el visitant; només les publicades.
  Sense resultats, la pantalla enllaça el contacte si és encès (RN-M07-12; `/ajuda/`).
"""

import unicodedata

from django.db import transaction
from django.http import Http404

from apps.core import audit
from apps.core.permissions import has_perm

from .models import FaqEntry, FaqTopic

PERMISSION = "website.help"  # WP4
TOPIC_FIELDS = {"name", "order"}
ENTRY_FIELDS = {"topic", "question", "answer", "order", "published"}
ACTION_PUBLISHED = "website.help_published"
ACTION_RETIRED = "website.help_retired"
ACTION_CHANGED = "website.help_changed"


def require(actor):
    if not has_perm(actor, PERMISSION, write=True):
        raise Http404


def _save(model, instance, fields, allowed, actor):
    require(actor)
    if set(fields) - allowed:
        raise ValueError(f"Camps no editables: {sorted(set(fields) - allowed)}")
    with transaction.atomic():
        # Des de la base de dades i bloquejada: un canvi rebutjat abans no s'arrossega, i una
        # edició simultània no torna a publicar una pregunta retirada.
        if instance is None:
            instance, old = model(), {}
        else:
            instance = model.objects.select_for_update().get(pk=instance.pk)
            old = {name: getattr(instance, name) for name in fields}
        for name, value in fields.items():
            setattr(instance, name, value)
        instance.full_clean()
        if old:
            instance.save(update_fields=list(fields))
        else:
            instance.save()
        if model is FaqEntry and old:
            _record(instance, old, fields, actor)
    return instance


def _record(entry, old, fields, actor) -> None:
    """RN-M07-14: publicar, retirar i cada camp canviat, amb el valor anterior."""
    for name, value in fields.items():
        before = old[name]
        if before == value:
            continue
        if name == "published":
            action = ACTION_PUBLISHED if value else ACTION_RETIRED
        else:
            action = ACTION_CHANGED
        before, value = (b.pk if hasattr(b, "pk") else b for b in (before, value))
        audit.record(action, actor=actor, target=entry, field=name, old=before, new=value)


def save_topic(topic: FaqTopic | None, *, actor, **fields) -> FaqTopic:
    return _save(FaqTopic, topic, fields, TOPIC_FIELDS, actor)


def save_entry(entry: FaqEntry | None, *, actor, **fields) -> FaqEntry:
    """Crea (sense publicar, si no es diu) o canvia una pregunta; `published` la publica o la
    retira de l'ajuda."""
    return _save(FaqEntry, entry, fields, ENTRY_FIELDS, actor)


def published_entries(topic: FaqTopic | None = None):
    entries = FaqEntry.objects.filter(published=True).select_related("topic")
    return entries.filter(topic=topic) if topic is not None else entries


def _fold(text: str) -> str:
    """Sense majúscules ni accents: «Quòta» troba «quota»."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def search(text: str) -> list[FaqEntry]:
    """RN-M07-12: cerca a la pregunta i a la resposta de les publicades."""
    wanted = _fold(text.strip())
    if not wanted:
        return []
    # shortcut: filtra en Python (unes desenes de preguntes); amb milers, `unaccent` a la consulta.
    return [
        e for e in published_entries() if wanted in _fold(e.question) or wanted in _fold(e.answer)
    ]
