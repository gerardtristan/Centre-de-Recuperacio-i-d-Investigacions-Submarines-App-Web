"""Titulacions d'una persona: lectura (T-M02-23; M02-6 i addenda de la 058; RN-M02-10, RN-M02-27,
RN-M02-28 i RN-M02-30).

Una titulació és un nivell (`CertificationLevel`, amb ordre) o una especialitat (una fitxa del
catàleg d'especialitats). Segons d'on ve i si algú l'ha comprovada, és:

- **verificada:** algú del club l'ha comprovada (`verified_by`);
- **del club:** surt d'un curs del club (`source = club_course`);
- **sense verificar:** declarada per la persona o importada, i ningú l'ha comprovada.

En mode de bloqueig només compten les verificades i les del club; en mode d'avís compten totes i
el responsable veu de quin origen és cadascuna (RN-M02-30).

**Són dades personals.** Aquest mòdul no comprova cap permís: no el crida cap vista. Qui mostri
una titulació ha de comprovar abans el permís que toqui (per a l'instructor, C3 i només dels
alumnes de les seves sessions).

**Fora d'aquesta peça:** carregar titulacions a mà i verificar-les (`certification_records`,
AC29), importar-les (T-M02-31, espera la mostra Q-23), crear la del club en emetre el certificat
(T-M02-19 i T-M02-31), el lligam amb el resultat del curs (`course_outcome`, quan existeixi) i
fer-les servir per als requisits d'una activitat (`requirements`, T-M02-29).
"""

from dataclasses import dataclass

from django.utils.translation import gettext as _

from .models import DiverCertification

VERIFIED = "verified"
CLUB = "club"
UNVERIFIED = "unverified"
ORIGIN_LABELS = {
    VERIFIED: _("verificada"),
    CLUB: _("d'un curs del club"),
    UNVERIFIED: _("sense verificar"),
}


def origin(certification) -> str:
    """`verified`, `club` o `unverified` (RN-M02-30)."""
    if certification.is_verified:
        return VERIFIED
    if certification.source == DiverCertification.Source.CLUB_COURSE:
        return CLUB
    return UNVERIFIED


def counts(certification, mode: str) -> bool:
    """Compta per complir un requisit? En bloqueig, només verificada o del club."""
    return mode != "block" or origin(certification) != UNVERIFIED


@dataclass(frozen=True)
class Held:
    """El que una persona té d'un requisit: la millor titulació que hi serveix."""

    certification: DiverCertification
    origin: str

    @property
    def origin_label(self) -> str:
        return str(ORIGIN_LABELS[self.origin])


def of(person):
    """Les titulacions de la persona, amb el nivell i l'especialitat carregats."""
    return DiverCertification.objects.filter(person=person).select_related("level", "speciality")


_BEST = {VERIFIED: 0, CLUB: 1, UNVERIFIED: 2}


def best(candidates) -> Held | None:
    held = sorted((Held(c, origin(c)) for c in candidates), key=lambda h: _BEST[h.origin])
    return held[0] if held else None


def level_held(person, minimum, *, certifications=None) -> Held | None:
    """La titulació de la persona que arriba al nivell `minimum` (el mateix `rank` o més alt,
    RN-M02-27), preferint la verificada, després la del club i després la que no ho és."""
    rows = of(person) if certifications is None else certifications
    return best(c for c in rows if c.level_id and c.level.rank >= minimum.rank)


def speciality_held(person, speciality, *, certifications=None) -> Held | None:
    rows = of(person) if certifications is None else certifications
    return best(c for c in rows if c.speciality_id == speciality.pk)
