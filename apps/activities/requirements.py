"""Càlcul dels requisits d'una activitat per a una persona (T-M02-29 i T-M02-32; RN-M02-10 i
RN-M02-27 a 33; CA-M02-31 i 32).

`check(activity, person)` diu, requisit per requisit, si la persona el compleix, i amb això si es
pot inscriure segons el mode de l'activitat:

- **Nivell mínim** (RN-M02-27): una titulació amb el mateix `rank` o més alt.
- **Especialitats** (RN-M02-28): totes (`all`) o alguna (`any`) de les exigides.
- **Llicència vigent** (RN-M02-10): `licences.current` el dia que comença l'activitat. Una en
  tràmit (RN-M06-13) no compleix: en `warn` es pot inscriure i el responsable la veu «en tràmit»;
  en `block`, no.
- **Edat mínima** (RN-M02-33): els anys complerts el dia d'inici. Sense data de naixement, «edat
  desconeguda»: el responsable ho veu marcat i no bloqueja (RN-M01-55), ni en `block`.

**Mode** (RN-M02-10 i 30). En `block`, qui no compleix un requisit no es pot inscriure, i només
compten les titulacions verificades o d'un curs del club. En `warn` es pot inscriure, compten totes
i el responsable veu el requisit marcat i de quin origen és la titulació.

**Privacitat.** El resultat només diu «compleix», «no compleix» o «no se sap» i un text curt; qui
el mostri ha de comprovar abans el seu permís. `required_level` (text) és informatiu: no es calcula.

**Fora d'aquesta peça:** fer-lo servir en inscriure's (T-M02-11) i els
requisits dels instructors (T-M02-30).
"""

from dataclasses import dataclass

from django.utils.translation import gettext as _

from apps.core.persons import age_on
from apps.licences import services as licences

from . import certifications
from .models import RequirementsMode, SpecialitiesRule

MET = "met"
NOT_MET = "not_met"
UNKNOWN = "unknown"

LEVEL = "level"
SPECIALITIES = "specialities"
LICENCE = "licence"
AGE = "age"


@dataclass(frozen=True)
class Check:
    """Un requisit i com hi queda la persona. `flagged`: el responsable l'ha de veure marcat
    encara que es compleixi (per exemple, una titulació sense verificar en mode d'avís)."""

    key: str
    state: str
    label: str
    detail: str = ""
    flagged: bool = False

    @property
    def met(self) -> bool:
        return self.state == MET


@dataclass(frozen=True)
class Result:
    mode: str
    checks: tuple[Check, ...]

    @property
    def met(self) -> bool:
        """Tots els requisits es compleixen (un «no se sap» no és complir)."""
        return all(check.met for check in self.checks)

    @property
    def blocking(self) -> tuple[Check, ...]:
        """Els requisits que impedeixen inscriure's: els que no es compleixen, en mode `block`."""
        if self.mode != RequirementsMode.BLOCK:
            return ()
        return tuple(check for check in self.checks if check.state == NOT_MET)

    @property
    def allowed(self) -> bool:
        return not self.blocking

    @property
    def warnings(self) -> tuple[Check, ...]:
        """El que el responsable ha de veure marcat."""
        return tuple(check for check in self.checks if not check.met or check.flagged)


def _level(activity, mode, held_rows) -> Check:
    minimum = activity.min_level
    label = _("Nivell mínim: %(level)s") % {"level": minimum.name}
    candidates = [c for c in held_rows if c.level_id and c.level.rank >= minimum.rank]
    counting = [c for c in candidates if certifications.counts(c, mode)]
    best = certifications.best(counting)
    if best is not None:
        unverified = best.origin == certifications.UNVERIFIED
        return Check(
            LEVEL,
            MET,
            label,
            _("Titulació %(origin)s.") % {"origin": best.origin_label},
            unverified,
        )
    if candidates:
        return Check(LEVEL, NOT_MET, label, _("Té la titulació, però sense verificar."))
    return Check(LEVEL, NOT_MET, label, _("No té cap titulació d'aquest nivell."))


def _specialities(activity, mode, held_rows, required) -> Check:
    rule = activity.specialities_rule
    names = ", ".join(entry.name for entry in required)
    if rule == SpecialitiesRule.ANY and len(required) > 1:
        label = _("Alguna d'aquestes especialitats: %(names)s") % {"names": names}
    else:
        label = _("Especialitats: %(names)s") % {"names": names}
    has, unverified, pending = [], False, False
    for entry in required:
        rows = [c for c in held_rows if c.speciality_id == entry.pk]
        best = certifications.best(c for c in rows if certifications.counts(c, mode))
        has.append(best is not None)
        unverified = unverified or (best is not None and best.origin == certifications.UNVERIFIED)
        pending = pending or (best is None and bool(rows))
    met = any(has) if rule == SpecialitiesRule.ANY else all(has)
    if met:
        detail = _("Alguna titulació és sense verificar.") if unverified else ""
        return Check(SPECIALITIES, MET, label, detail, unverified)
    if pending:
        return Check(SPECIALITIES, NOT_MET, label, _("En té alguna, però sense verificar."))
    return Check(SPECIALITIES, NOT_MET, label, _("Li falten especialitats."))


def _licence(activity, person) -> Check:
    """Mai la categoria, el número ni la data de caducitat: només si és vigent."""
    label = _("Llicència vigent")
    info = licences.current(person, activity.starts_on)
    if info is None:
        return Check(
            LICENCE, NOT_MET, label, _("No consta cap llicència vigent el dia de l'activitat.")
        )
    if info.status == licences.CurrentStatus.IN_PROGRESS:
        return Check(LICENCE, NOT_MET, label, _("En tràmit."))
    return Check(LICENCE, MET, label)


def _age(activity, person) -> Check:
    """Mai la data de naixement ni l'edat: només si arriba al mínim."""
    label = _("Edat mínima: %(age)s anys") % {"age": activity.min_age}
    birth, day = person.birth_date, activity.starts_on
    if birth is None or birth > day:
        return Check(AGE, UNKNOWN, label, _("Edat desconeguda."), True)
    if age_on(birth, day) >= activity.min_age:
        return Check(AGE, MET, label)
    return Check(AGE, NOT_MET, label, _("No arriba a l'edat mínima."))


def check(activity, person, *, mode=None) -> Result:
    """Els requisits de `activity` per a `person`. `mode` és el de l'activitat, tret que se'n doni
    un altre (per ensenyar al responsable què passaria amb l'altre mode)."""
    mode = mode or activity.requirements_mode
    checks = []
    required = list(activity.required_specialities.all())
    held_rows = list(certifications.of(person)) if activity.min_level_id or required else []
    if activity.min_level_id:
        checks.append(_level(activity, mode, held_rows))
    if required:
        checks.append(_specialities(activity, mode, held_rows, required))
    if activity.licence_required:
        checks.append(_licence(activity, person))
    if activity.min_age:
        checks.append(_age(activity, person))
    return Result(mode, tuple(checks))
