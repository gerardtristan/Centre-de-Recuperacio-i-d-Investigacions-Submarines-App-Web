"""Dades públiques de les activitats (T-M02-08; M02-8, `get_activity` i `public_list`; AC1;
CA-M02-05; RN-M02-24 i RN-M02-45; CA-M02-48; M02-12, «mínim de dades»).

El que veu qualsevol visitant, i el que consumiran altres mòduls (07, 03 i 09) sense tocar els
models del 02.

- **Què és públic:** una activitat publicada i encara no acabada ni cancel·lada: oberta, tancada
  a inscripcions o en curs. Un esborrany, una de cancel·lada o una d'acabada no ho és: qui en
  demana el detall rep «no trobat», sense saber si existeix (CA-M02-05).
- **Què se'n diu:** només dades de l'activitat. Cap nom de persona: ni inscrits, ni instructors,
  ni la persona responsable. Del programa, la funció de qui se n'encarrega, que mai és un nom.
- **Previsió marítima** (RN-M02-24): només l'enllaç que el responsable ha posat a la sortida.
  Cap giny ni cap script d'un tercer.
- **Lloc** (RN-M02-45, CA-M02-48): només el nom. Mai les notes del lloc, el centre habitual, la
  còpia estàndard del preu ni el cost de material.

**Concrecions d'implementació** (dins de les regles; al diari de la T-M02-08)

- El llistat no mostra una activitat la data de final de la qual ja ha passat, encara que ningú
  l'hagi marcada com a feta.
- Les sessions cancel·lades no surten.

- **Places lliures** (P-M02-A pas 1, HU-M02-06): només el nombre, amb el mateix criteri que la
  inscripció (`enrolment.free_places`: places menys les inscripcions que ocupen plaça). Mai qui hi
  és inscrit.

**Activitats fetes i fotos per a la web** (T-M02-53; RP-M07-02, addenda M07 de la 106; RN-M02-23;
RN-M07-21 i 22):

- `public_past_list(filters)`: les activitats publicades (`published_at`) que ja s'han fet:
  finalitzades, tancades econòmicament o publicades amb la data de final passada. Mai una de
  cancel·lada ni un esborrany. Les mateixes dades sense noms que `public_list`, de la més recent
  a la més antiga. `filters`, com els desa el bloc del 07: `type` (`course` o `outing`) i
  `department` (enter); un valor no vàlid s'ignora.
- `publishable_photos(activity)`: només les fotos de medi ambient actives, marcades com a
  publicables (CA-M02-22) i que encara compleixen autor, permís i, si hi surten persones,
  consentiment, d'una activitat feta i publicada. Amb `activities.environment_photos_enabled`
  apagat (P-41), cap. Mai carnets de titulació (104), avatars ni documents: no surten d'aquí.
  Sense l'autor (és un nom; P-690) i amb un text alternatiu fet amb el títol de l'activitat.

**Fora d'aquesta peça:** el preu «que
et correspon» segons si ets soci i el botó d'inscriure's (T-M02-11 i T-M02-14) i l'enllaç al
butlletí quan no hi ha cap activitat (mòdul 07). Una sortida sense enllaç propi a la previsió fa
servir el de l'ajust `activities.marine_forecast_url` (VC-25, RN-M02-24; T-M02-28b).
"""

import datetime
from dataclasses import dataclass, field

from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import business_settings
from apps.core.charges import euros

from . import enrolment, environment_photos
from .models import Activity, EnvironmentalPhoto

S = Activity.Status
PUBLIC_STATUSES = (S.OPEN, S.REGISTRATION_CLOSED, S.IN_PROGRESS)
DONE_STATUSES = (S.DONE, S.CLOSED)
FORECAST_KEY = "activities.marine_forecast_url"  # VC-25


class NotFound(Exception):
    """L'activitat no existeix o no és pública (M02-8). No es diu quin dels dos casos és."""


@dataclass(frozen=True)
class PublicSession:
    kind: str
    starts_at: datetime.datetime
    ends_at: datetime.datetime
    place: str


@dataclass(frozen=True)
class PublicBlock:
    starts_at: datetime.time
    ends_at: datetime.time | None
    label: str
    place: str
    responsible_label: str


@dataclass(frozen=True)
class PublicActivity:
    """Tot el que es pot ensenyar d'una activitat a qui no ha entrat. Cap dada personal."""

    pk: int
    kind: str
    kind_label: str
    title: str
    description: str
    type_label: str
    starts_on: datetime.date
    ends_on: datetime.date
    place: str
    meeting_point: str
    max_places: int
    free_places: int
    price_member: str
    price_non_member: str
    open_to_non_members: bool
    required_level: str
    min_level: str
    specialities: tuple[str, ...]
    any_speciality: bool
    min_age: int | None
    licence_required: bool
    registration_open: bool
    registration_closes_at: datetime.datetime
    forecast_url: str
    sessions: tuple[PublicSession, ...] = field(default=())
    blocks: tuple[PublicBlock, ...] = field(default=())


def _public(today):
    return Activity.objects.filter(status__in=PUBLIC_STATUSES, ends_on__gte=today)


def _name(place) -> str:
    return place.name if place is not None else ""


def _data(activity, *, detail: bool) -> PublicActivity:
    sessions, blocks = (), ()
    if detail:
        sessions = tuple(
            PublicSession(s.get_kind_display(), s.starts_at, s.ends_at, _name(s.place))
            for s in activity.sessions.filter(cancelled=False).select_related("place")
        )
        blocks = tuple(
            PublicBlock(b.starts_at, b.ends_at, b.label, _name(b.shown_place), b.responsible_label)
            for b in activity.programme_blocks.select_related("place")
        )
    if activity.kind == Activity.Kind.COURSE:
        type_label = activity.catalogue_entry.get_kind_display()
    else:
        type_label = activity.outing_type.name
        if activity.subtype_id:
            type_label = f"{type_label} · {activity.subtype.name}"
    return PublicActivity(
        pk=activity.pk,
        kind=activity.kind,
        kind_label=activity.get_kind_display(),
        title=activity.title,
        description=activity.description,
        type_label=type_label,
        starts_on=activity.starts_on,
        ends_on=activity.ends_on,
        place=_name(activity.place),
        meeting_point=activity.meeting_point,
        max_places=activity.max_places,
        free_places=enrolment.free_places(activity),
        price_member=euros(activity.price_member_cents),
        price_non_member=euros(activity.price_non_member_cents),
        open_to_non_members=activity.open_to_non_members,
        required_level=activity.required_level,
        min_level=activity.min_level.name if activity.min_level_id else "",
        specialities=tuple(e.name for e in activity.required_specialities.all()),
        any_speciality=activity.specialities_rule == "any",
        min_age=activity.min_age,
        licence_required=activity.licence_required,
        registration_open=activity.status == S.OPEN,
        registration_closes_at=activity.registration_closes_at,
        forecast_url=_forecast_url(activity),
        sessions=sessions,
        blocks=blocks,
    )


def _forecast_url(activity) -> str:
    """RN-M02-24: només per a les sortides; la de la sortida o, si no en té, la de l'ajust."""
    if activity.kind != Activity.Kind.OUTING:
        return ""
    return activity.forecast_url or business_settings.get(FORECAST_KEY)


def public_list(*, kind: str = "", today=None) -> list[PublicActivity]:
    """Les activitats publicades, de la més propera a la més llunyana. `kind`: `course`,
    `outing` o buit per a totes."""
    activities = _public(today or timezone.localdate())
    if kind in Activity.Kind.values:
        activities = activities.filter(kind=kind)
    activities = activities.select_related(
        "catalogue_entry", "outing_type", "subtype", "place", "min_level"
    )
    return [_data(a, detail=False) for a in activities.order_by("starts_on", "pk")]


def get_activity(pk, *, today=None) -> PublicActivity:
    """Les dades públiques d'una activitat. `NotFound` si no existeix o no és pública."""
    activity = (
        _public(today or timezone.localdate())
        .select_related("catalogue_entry", "outing_type", "subtype", "place", "min_level")
        .filter(pk=pk)
        .first()
    )
    if activity is None:
        raise NotFound
    return _data(activity, detail=True)


@dataclass(frozen=True)
class PublicPhoto:
    """Una foto que el 07 pot posar a la web (RN-M07-22). Cap nom: ni l'autor ni qui hi surt."""

    pk: int
    activity: int
    content_type: str
    alt_text: str


_SELECT = ("catalogue_entry", "outing_type", "subtype", "place", "min_level")


def _past(today):
    return Activity.objects.filter(published_at__isnull=False).filter(
        Q(status__in=DONE_STATUSES) | Q(status__in=PUBLIC_STATUSES, ends_on__lt=today)
    )


def public_past_list(filters=None, *, today=None) -> list[PublicActivity]:
    """Les activitats fetes i publicades (RP-M07-02), de la més recent a la més antiga."""
    filters = filters or {}
    activities = _past(today or timezone.localdate())
    if filters.get("type") in Activity.Kind.values:
        activities = activities.filter(kind=filters["type"])
    department = filters.get("department")
    # Un valor que no és un identificador vàlid s'ignora: mai un error a la web pública.
    if type(department) is int and 0 < department < 2**63:
        activities = activities.filter(department_id=department)
    activities = activities.select_related(*_SELECT).order_by("-ends_on", "-pk")
    return [_data(a, detail=False) for a in activities]


def publishable_photos(activity, *, today=None) -> list[PublicPhoto]:
    """Les fotos publicables d'una activitat feta i publicada (RP-M07-02; RN-M02-23)."""
    if not environment_photos.enabled():  # P-41: apagat, cap foto
        return []
    pk = getattr(activity, "pk", activity)
    found = _past(today or timezone.localdate()).filter(pk=pk).first()
    if found is None:
        return []
    photos = (
        EnvironmentalPhoto.objects.filter(
            result__activity=found,
            status=EnvironmentalPhoto.Status.ACTIVE,
            publishable=True,
            usage_permission=True,
        )  # fmt: skip
        .exclude(author__regex=r"^\s*$")
        .exclude(shows_people=True, people_consent=False)
    )
    alt = _("Foto de l'activitat «%(title)s»") % {"title": found.title}
    return [PublicPhoto(p.pk, found.pk, p.content_type, alt) for p in photos]
