"""Patrons i blocs compartits (T-M07-20a, decisió 106): dades, amb versions com les pàgines.

- `save_pattern(name, blocks, actor)`: un patró nou o una versió nova del que té aquest nom.
- `save_shared(shared, block, actor)`: un bloc compartit nou (`shared` és el nom) o una versió
  nova d'un que ja existeix (`shared` és el `SharedBlock`).
- `pattern_blocks(pattern)` i `resolve(blocks)`: el contingut vigent, per inserir un patró (en
  queda una còpia a la pàgina) i per pintar o publicar una pàgina amb blocs compartits (cada
  referència pren el contingut de l'última versió i hi conserva el seu `hidden`).

Tot demana WP1 (fa de WP10 i WP9 fins que el torn del nucli els separi, T-M07-21 i T-M07-26) i
queda al registre amb la versió anterior.
"""

import copy

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max, Q
from django.utils.translation import gettext as _

from apps.core import audit

from . import blocks as catalog
from .models import Pattern, PatternVersion, SharedBlock, SharedBlockVersion
from .pages import require

ACTION_PATTERN = "website.pattern_saved"
ACTION_SHARED = "website.shared_block_saved"
MISSING = {"kind": "divider", "hidden": True}  # un compartit que ja no hi és no pinta res


def _name(name: str) -> str:
    name = (name or "").strip()
    if not name or len(name) > 100:
        raise ValidationError(_("Cal un nom de fins a 100 caràcters."))
    return name


def _version(owner, model, field: str, actor, **content):
    """Crea la versió següent (l'amo ja és bloquejat) i ho apunta al registre."""
    previous = model.objects.filter(**{field: owner}).aggregate(n=Max("number"))["n"] or 0
    version = model.objects.create(**{field: owner}, number=previous + 1, created_by=actor,
                                   **content)  # fmt: skip
    action = ACTION_PATTERN if model is PatternVersion else ACTION_SHARED
    audit.record(action, actor=actor, target=owner, field="version", old=previous or None,
                 new=version.number)  # fmt: skip
    return version


@transaction.atomic
def save_pattern(name: str, blocks: list, actor) -> PatternVersion:
    require(actor)
    catalog.validate(blocks, publishing=False)
    pattern, _created = Pattern.objects.get_or_create(name=_name(name))
    pattern = Pattern.objects.select_for_update().get(pk=pattern.pk)
    return _version(pattern, PatternVersion, "pattern", actor, blocks=catalog.upgrade_all(blocks))


@transaction.atomic
def save_shared(shared, block: dict, actor) -> SharedBlockVersion:
    require(actor)
    if not isinstance(block, dict) or any(b.get("kind") == "shared"
                                          for b in catalog.walk([block])):  # fmt: skip
        raise ValidationError(_("Un bloc compartit no pot ser una referència a un altre."))
    block = {k: v for k, v in block.items() if k != "hidden"}  # amagar-lo és de cada pàgina
    catalog.validate([block], publishing=False)
    if isinstance(shared, SharedBlock):
        shared = SharedBlock.objects.select_for_update().get(pk=shared.pk)
    else:
        if SharedBlock.objects.filter(name=_name(shared)).exists():
            raise ValidationError(_("Ja hi ha un bloc compartit amb aquest nom."))
        shared = SharedBlock.objects.create(name=_name(shared))
    return _version(shared, SharedBlockVersion, "shared", actor, block=block)


def pattern_blocks(pattern: Pattern) -> list:
    version = pattern.versions.order_by("-number").first()
    return copy.deepcopy(version.blocks) if version else []


def _latest(ids):
    return SharedBlockVersion.objects.filter(shared_id__in=set(ids)).order_by(
        "shared_id", "-number").distinct("shared_id")  # fmt: skip


def current_shared(ids) -> dict:
    """{id: bloc} amb l'última versió de cada bloc compartit."""
    return {v.shared_id: v.block for v in _latest(ids)}


def _refs(blocks):
    return [b for b in catalog.walk(blocks) if b.get("kind") == "shared"]


def _map(blocks, one):
    """`one` a cada bloc, també dins de les seccions; la llista i les posicions no canvien."""

    def each(block):
        if block.get("kind") == "section":
            columns = [[each(b) for b in column] for column in block.get("columns") or []]
            return one({**block, "columns": columns})
        return one(block)

    return [each(block) for block in blocks]


def pin(blocks: list, *, repin: bool = False) -> list:
    """En publicar: cada referència queda amb la versió del compartit que es publica (la
    vigent). `repin`: també les que ja en tenien una (publicar l'esborrany); sense, es conserven
    (tornar a una versió anterior en recupera el contingut d'aleshores)."""
    newest = {v.shared_id: v.number for v in _latest(r.get("shared") for r in _refs(blocks))}

    def one(block):
        if block.get("kind") != "shared" or block.get("shared") not in newest:
            return block
        if block.get("version") and not repin:
            return block
        return {**block, "version": newest[block["shared"]]}

    return _map(blocks, one)


def resolve(blocks: list, *, latest: bool = False) -> list:
    """Les referències, amb el seu contingut: la versió fixada en publicar o, a l'esborrany
    (`latest`) i a les referències sense versió, la vigent. Conserven el seu `hidden`."""
    refs = _refs(blocks)
    newest = current_shared(r.get("shared") for r in refs)
    wanted = {(r.get("shared"), r.get("version")) for r in refs if r.get("version")}
    pinned = {}
    if wanted and not latest:
        query = Q()
        for shared, number in wanted:
            query |= Q(shared_id=shared, number=number)
        pinned = {(v.shared_id, v.number): v.block
                  for v in SharedBlockVersion.objects.filter(query)}  # fmt: skip

    def one(block):
        if block.get("kind") != "shared":
            return block
        key = (block.get("shared"), block.get("version"))
        content = pinned.get(key) if key in pinned else newest.get(block.get("shared"))
        content = content or MISSING
        return {**content, "hidden": block.get("hidden", False) or content.get("hidden", False)}

    return _map(blocks, one)
