"""Preguntes freqüents amb cercador (T-M07-09; M07b, P-M07-G, RN-M07-12; CA-M07-16).

- `save_topic` i `save_entry`: WP4 (`website.help`, «Sí») al servidor.
- `published_entries(topic)` i `search(text)`: el que veu el visitant; només les publicades.
  Sense resultats, la pantalla enllaça el contacte si és encès (RN-M07-12; `/ajuda/`).
"""

import unicodedata

from django.http import Http404

from apps.core.permissions import has_perm

from .models import FaqEntry, FaqTopic

PERMISSION = "website.help"  # WP4
TOPIC_FIELDS = {"name", "order"}
ENTRY_FIELDS = {"topic", "question", "answer", "order", "published"}


def require(actor):
    if not has_perm(actor, PERMISSION, write=True):
        raise Http404


def _save(model, instance, fields, allowed, actor):
    require(actor)
    if set(fields) - allowed:
        raise ValueError(f"Camps no editables: {sorted(set(fields) - allowed)}")
    # Des de la base de dades: un canvi rebutjat abans no s'arrossega.
    instance = model.objects.get(pk=instance.pk) if instance else model()
    for name, value in fields.items():
        setattr(instance, name, value)
    instance.full_clean()
    instance.save()
    return instance


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
