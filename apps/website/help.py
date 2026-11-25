"""Preguntes freqüents amb cercador (T-M07-09; M07b, P-M07-G, RN-M07-12; CA-M07-16).

- `save_topic` i `save_entry`: WP4 (`website.help`, «Sí») al servidor, amb la fila bloquejada;
  publicar, retirar i canviar una pregunta queden al registre amb el valor anterior (RN-M07-14).
- `published_entries(topic)` i `search(text)`: el que veu el visitant; només les publicades.
- Tutorials (T-M07-10): `save_tutorial` (WP4), els publicats i `tutorial_for(screen_code)`, que
  fa servir l'etiqueta `{% mira_com_es_fa %}` de qualsevol pantalla (RN-M07-11).
  Sense resultats, la pantalla enllaça el contacte si és encès (RN-M07-12; `/ajuda/`).
"""

import unicodedata

from django.db import transaction
from django.http import Http404

from apps.core import audit
from apps.core.permissions import has_perm

from . import media
from .models import FaqEntry, FaqTopic, Tutorial

PERMISSION = "website.help"  # WP4
TOPIC_FIELDS = {"name", "order"}
ENTRY_FIELDS = {"topic", "question", "answer", "order", "published"}
ACTION_PUBLISHED = "website.help_published"
ACTION_RETIRED = "website.help_retired"
ACTION_CHANGED = "website.help_changed"
TUTORIAL_FIELDS = {"title", "slug", "steps", "image", "screen_code", "order", "published"}
# T-M07-10 (RN-M07-14): les mateixes accions per als tutorials, amb el seu nom.
TUTORIAL_PUBLISHED = "website.tutorial_published"
TUTORIAL_RETIRED = "website.tutorial_retired"
TUTORIAL_CHANGED = "website.tutorial_changed"
_ACTIONS = {
    "FaqEntry": (ACTION_PUBLISHED, ACTION_RETIRED, ACTION_CHANGED),
    "Tutorial": (TUTORIAL_PUBLISHED, TUTORIAL_RETIRED, TUTORIAL_CHANGED),
}


def require(actor):
    if not has_perm(actor, PERMISSION, write=True):
        raise Http404


def _save(model, instance, fields, allowed, actor, check=None):
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
        if check is not None:
            check(instance)
        if old:
            instance.save(update_fields=list(fields))
        else:
            instance.save()
        if model.__name__ in _ACTIONS and old:
            _record(instance, old, fields, actor)
    return instance


def _record(entry, old, fields, actor) -> None:
    """RN-M07-14: publicar, retirar i cada camp canviat, amb el valor anterior."""
    for name, value in fields.items():
        before = old[name]
        if before == value:
            continue
        published, retired, changed = _ACTIONS[type(entry).__name__]
        if name == "published":
            action = published if value else retired
        else:
            action = changed
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


# --- Tutorials (T-M07-10; RN-M07-11, CA-M07-17) ---------------------------------------------


def save_tutorial(tutorial: Tutorial | None, *, actor, **fields) -> Tutorial:
    """WP4. Un tutorial publicat no porta cap foto que no es pugui publicar (RN-M07-05)."""
    return _save(Tutorial, tutorial, fields, TUTORIAL_FIELDS, actor, check=_check_image)


def _check_image(tutorial: Tutorial) -> None:
    if tutorial.published and tutorial.image_id is not None:
        media.check_publishable([str(tutorial.image.key)])


def published_tutorials():
    return Tutorial.objects.filter(published=True).select_related("image")


def get_published_tutorial(slug: str) -> Tutorial:
    tutorial = published_tutorials().filter(slug=slug).first()
    if tutorial is None:
        raise Http404
    return tutorial


def tutorial_for(screen_code: str) -> Tutorial | None:
    """M07-8: el tutorial publicat d'una pantalla (el primer per ordre), o res."""
    if not screen_code:
        return None
    return published_tutorials().filter(screen_code=screen_code).first()
