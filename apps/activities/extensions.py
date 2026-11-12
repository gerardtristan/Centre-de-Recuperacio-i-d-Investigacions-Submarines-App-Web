"""Punts d'extensió i senyals del 02 (T-M02-09; M02-8, «Punts d'extensió i senyals»).

Perquè el 03 i altres mòduls s'enganxin al 02 sense que el 02 els importi. Cada mòdul es registra
des del seu `AppConfig.ready()`; el 02 només llegeix el que hi ha registrat.

**Registres**

- `register_enrolment_section(section)`: preguntes que s'afegeixen al formulari d'inscripció (el 03
  hi posarà el material que es porta i el que cal). El formulari és de la T-M02-11.
- `register_closing_check(check)`: motius que impedeixen tancar una activitat (el 03 hi posarà
  «material pendent»). Els motius propis del 02 i `closing_blockers` són de la T-M02-22.
- `register_detail_section(section)`: un bloc a «Les meves activitats» i a la fitxa d'administració
  (el 03 hi posarà el material assignat). Les pantalles són de la T-M02-06 i la T-M02-22.

**Senyals** (de Django, enviats dins la mateixa transacció que el canvi)

- `activity_done(activity, by)`: l'envia `states.mark_done`.
- `activity_duplicated(original, copy, by)`: l'enviarà la T-M02-07.
- `enrolment_confirmed(enrolment)`: l'enviarà la T-M02-10.

Les cancel·lacions (`enrolment.cancelled` i `activity.cancelled`) no són senyals: són esdeveniments
de la 049 amb registre de lliuraments (RN-M02-36; T-M02-35).

**Concrecions d'implementació** (dins de les regles; al diari de la T-M02-09)

- Cada secció té una clau única. Registrar-ne dues amb la mateixa clau és un error de programació.
- L'ordre és el de registre.
- Un senyal s'envia amb `send`: si un mòdul subscrit falla, el canvi es desfà sencer. Val més no
  marcar una activitat com a feta que deixar el material sense avisar.
- Una comprovació de tancament que falla tampoc es calla: l'error puja i l'activitat no es tanca.
- Qui registra una secció de detall respon de no mostrar-hi res que qui mira no pugui veure: rep
  qui mira (`viewer`) i el lloc (`place`), i pot tornar `None` per no mostrar res.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from django.core.exceptions import ImproperlyConfigured
from django.dispatch import Signal

PLACE_PERSONAL = "personal"  # «Les meves activitats» (compte personal o enllaç de convidat)
PLACE_ADMIN = "admin"  # fitxa de l'activitat a l'administració
PLACES = (PLACE_PERSONAL, PLACE_ADMIN)

activity_done = Signal()  # activity, by
activity_duplicated = Signal()  # original, copy, by
enrolment_confirmed = Signal()  # enrolment


@dataclass(frozen=True)
class EnrolmentSection:
    """Preguntes d'un altre mòdul al formulari d'inscripció.

    - `fields(activity, person)`: camps de formulari de Django, per nom. Buit = no hi afegeix res.
    - `save(enrolment, data)`: desa les respostes validades, dins la transacció de la inscripció.
    """

    key: str
    label: str
    fields: Callable[..., Mapping]
    save: Callable[..., None]


@dataclass(frozen=True)
class DetailSection:
    """Un bloc d'un altre mòdul a la fitxa d'una activitat.

    - `context(activity, place=…, viewer=…, person=…)`: dades per a `template_name`, o `None` si
      aquí no ha de sortir res. `person` és el participant a «Les meves activitats».
    """

    key: str
    label: str
    template_name: str
    context: Callable[..., Mapping | None]


_enrolment_sections: dict[str, EnrolmentSection] = {}
_detail_sections: dict[str, DetailSection] = {}
_closing_checks: list[Callable[..., list[str]]] = []


def _is_a(section, kind) -> None:
    if not isinstance(section, kind):
        raise ImproperlyConfigured(f"S'esperava un {kind.__name__}.")


def _add(registry: dict, section) -> None:
    if not section.key or not str(section.label):
        raise ImproperlyConfigured("Una secció necessita clau i títol.")
    if section.key in registry:
        raise ImproperlyConfigured(f"Ja hi ha una secció amb la clau «{section.key}».")
    registry[section.key] = section


def register_enrolment_section(section: EnrolmentSection) -> None:
    _is_a(section, EnrolmentSection)
    if not callable(section.fields) or not callable(section.save):
        raise ImproperlyConfigured("Una secció d'inscripció necessita `fields` i `save`.")
    _add(_enrolment_sections, section)


def enrolment_sections() -> list[EnrolmentSection]:
    return list(_enrolment_sections.values())


def register_detail_section(section: DetailSection) -> None:
    _is_a(section, DetailSection)
    if not callable(section.context) or not section.template_name:
        raise ImproperlyConfigured("Una secció de detall necessita plantilla i `context`.")
    _add(_detail_sections, section)


def detail_sections(activity, *, place, viewer=None, person=None) -> list[tuple]:
    """(secció, context) de cada secció que té alguna cosa a mostrar en aquest lloc."""
    if place not in PLACES:
        raise ImproperlyConfigured(f"Lloc desconegut: {place}")
    shown = []
    for section in _detail_sections.values():
        context = section.context(activity, place=place, viewer=viewer, person=person)
        if context is not None:
            shown.append((section, context))
    return shown


def register_closing_check(check: Callable[..., list[str]]) -> None:
    """`check(activity)` torna els motius (text) que impedeixen tancar; llista buida = cap."""
    if not callable(check):
        raise ImproperlyConfigured("Una comprovació de tancament ha de ser una funció.")
    if check not in _closing_checks:
        _closing_checks.append(check)


def closing_reasons(activity) -> list[str]:
    """Motius dels altres mòduls que impedeixen tancar l'activitat, en l'ordre de registre."""
    reasons = []
    for check in _closing_checks:
        reasons.extend(str(reason) for reason in check(activity))
    return reasons
