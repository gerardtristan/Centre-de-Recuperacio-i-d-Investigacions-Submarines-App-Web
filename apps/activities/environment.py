"""Resultats ambientals i fitxa de projecte (T-M02-20; P-M02-G; M02-6; RN-M02-23; CA-M02-21).

- **Resultats** (`record_results`): després d'una sortida de medi ambient, els quilos de residus
  (es desen en grams), les espècies observades (una per línia) i observacions. Un sol registre per
  sortida, que es pot corregir: cada canvi queda al registre d'activitat amb el valor anterior.
- **Fitxa del projecte** (`project_summary`): les sortides del projecte, la suma de residus i les
  espècies de totes. Les factures i l'ajut del projecte hi apareixeran amb el 09.
- **Permís:** AC14 (`activities.environment.manage`). Amb edició, registrar; amb «Cons.» (la
  Junta, a la configuració inicial), només veure. Sense, «no trobat».
- **Res d'això es publica** des del 02 (RN-M02-23): cap pàgina pública no ho mostra.

**Concrecions d'implementació** (dins de les regles; al diari de la T-M02-20)

- Els resultats es registren quan la sortida ja s'ha fet (`done` o tancada econòmicament): el
  procés diu «després d'una sortida».
- Les espècies es desen netes: sense línies buides ni repetides.
- Les dades que es registren són les del supòsit S-M02-14 (residus, espècies i observacions)
  [A validar: junta].

**Fora d'aquesta peça: les fotos** (`EnvironmentalPhoto`, CA-M02-22). Necessiten dues coses que
encara no hi són: que els fitxers privats de la 00 admetin fitxers d'un mòdul (ara només
l'exportació RGPD) i treure la geolocalització de les fotos en pujar-les (M02-12), que demana una
dependència nova. Cap codi no ho simula.
"""

from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit

from . import permissions
from .models import Activity, EnvironmentalResult

RESULTS_RECORDED = "activities.environment.results_recorded"
RESULTS_UPDATED = "activities.environment.results_updated"
MAX_GRAMS = 100_000_000  # 100 tones: més que això és un error d'escriptura
MAX_TEXT = 2000
RECORDABLE = (Activity.Status.DONE, Activity.Status.CLOSED)
FIELDS = ("waste_grams", "species", "observations")


def is_environmental(activity) -> bool:
    return (
        activity.kind == Activity.Kind.OUTING
        and activity.outing_type_id is not None
        and activity.outing_type.is_environmental
    )


def can_record(activity) -> bool:
    """La sortida és de medi ambient i ja s'ha fet."""
    return is_environmental(activity) and activity.status in RECORDABLE


def kilos(grams: int | None) -> str:
    """Els grams com a quilos, amb coma i fins a tres decimals: 24750 → «24,75 kg»."""
    if grams is None:
        return ""
    whole, rest = divmod(grams, 1000)
    decimals = f"{rest:03d}".rstrip("0")
    return f"{whole},{decimals} kg" if decimals else f"{whole} kg"


def clean_species(text) -> str:
    """Una espècie per línia, sense línies buides ni repetides (es conserva l'ordre)."""
    seen, lines = set(), []
    for raw in (text or "").splitlines():
        name = " ".join(raw.split())
        if name and name.casefold() not in seen:
            seen.add(name.casefold())
            lines.append(name)
    return "\n".join(lines)


def results_for(activity) -> EnvironmentalResult | None:
    return EnvironmentalResult.objects.filter(activity=activity).first()


@transaction.atomic
def record_results(
    activity, *, by, waste_grams=None, species="", observations="", now=None, request=None
) -> EnvironmentalResult:
    """Desa els resultats de la sortida, o els corregeix si ja n'hi havia."""
    permissions.require(by, permissions.ENVIRONMENT)
    locked = (
        Activity.objects.select_for_update(of=("self",))
        .select_related("outing_type")
        .get(pk=activity.pk)
    )
    if not is_environmental(locked):
        raise ValidationError(_("Només les sortides de medi ambient tenen resultats ambientals."))
    if locked.status not in RECORDABLE:
        raise ValidationError(_("Els resultats es registren quan la sortida ja s'ha fet."))
    if waste_grams is not None and (
        isinstance(waste_grams, bool)
        or not isinstance(waste_grams, int)
        or not 0 <= waste_grams <= MAX_GRAMS
    ):
        raise ValidationError(_("Els residus han de ser una quantitat de quilos, zero o més."))
    new = {
        "waste_grams": waste_grams,
        "species": clean_species(species),
        "observations": (observations or "").strip(),
    }
    if len(new["species"]) > MAX_TEXT or len(new["observations"]) > MAX_TEXT:
        raise ValidationError(
            _("El text és massa llarg (màxim, %(max)s caràcters).") % {"max": MAX_TEXT}
        )
    result = EnvironmentalResult.objects.select_for_update().filter(activity=locked).first()
    if result is None:
        result = EnvironmentalResult.objects.create(
            activity=locked, recorded_by=by, recorded_at=now or timezone.now(), **new
        )
        audit.record(
            RESULTS_RECORDED,
            actor=by,
            target=result,
            details={"activity": locked.pk, "waste_grams": waste_grams},
            request=request,
        )
        return result
    changes = {name: (getattr(result, name), new[name]) for name in FIELDS}
    changed = audit.record_changes(
        RESULTS_UPDATED, actor=by, target=result, changes=changes, request=request
    )
    if changed:
        for name in FIELDS:
            setattr(result, name, new[name])
        result.recorded_by, result.recorded_at = by, now or timezone.now()
        result.save(update_fields=[*FIELDS, "recorded_by", "recorded_at"])
    return result


@dataclass(frozen=True)
class ProjectSummary:
    """El que acumula un projecte: les seves sortides i els resultats de totes."""

    outings: tuple  # (activitat, resultat o None)
    total_grams: int
    species: tuple[str, ...]
    with_results: int

    @property
    def total_kilos(self) -> str:
        return kilos(self.total_grams)


def project_summary(project) -> ProjectSummary:
    """Sortides del projecte, de la més recent a la més antiga, amb la suma de residus en grams
    i totes les espècies observades, sense repetir."""
    activities = (
        project.activities.select_related("outing_type", "subtype", "environmental_result")
        .order_by("-starts_on", "-pk")
        .all()
    )
    rows, total, with_results, seen, species = [], 0, 0, set(), []
    for activity in activities:
        result = getattr(activity, "environmental_result", None)
        rows.append((activity, result))
        if result is None:
            continue
        with_results += 1
        total += result.waste_grams or 0
        for name in result.species.splitlines():
            if name.casefold() not in seen:
                seen.add(name.casefold())
                species.append(name)
    return ProjectSummary(
        tuple(rows), total, tuple(sorted(species, key=str.casefold)), with_results
    )
