"""Centre habitual d'un lloc i proposta de centre (T-M03-26; RN-M03-23 i 24; CA-M03-23).

El bloc del formulari del lloc (`activities.register_place_section`) espera que el 02 tingui
aquest punt d'extensió i les plantilles: aquí hi ha el servei que el bloc cridarà."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext_lazy as _

from apps.core import audit
from apps.core.permissions import has_perm

from .models import PlaceUsualCentre

PLACES = "activities.places.manage"  # AC22
USUAL_CENTRE_CHANGED = "equipment.usual_centre_changed"


@transaction.atomic
def set_usual_centre(place, centre, *, by) -> PlaceUsualCentre | None:
    """Tria (o treu, amb `None`) el centre habitual del lloc. Només centres actius (RN-M03-23)."""
    if not has_perm(by, PLACES, write=True):
        raise Http404
    if centre is not None and not centre.active:
        raise ValidationError(_("Només es pot triar un centre actiu."))
    current = PlaceUsualCentre.objects.select_for_update().filter(place=place).first()
    old = current.centre.name if current else None
    if centre is None:
        if current is not None:
            current.delete()
        result = None
    else:
        result = current or PlaceUsualCentre(place=place)
        result.centre, result.changed_by = centre, by
        result.save()
    audit.record(
        USUAL_CENTRE_CHANGED,
        actor=by,
        target=place,
        field="usual_centre",
        old=old,
        new=centre.name if centre else None,
    )
    return result


def usual_centre(place):
    row = PlaceUsualCentre.objects.select_related("centre").filter(place=place).first()
    return row.centre if row else None


def usual_centre_inactive(place) -> bool:
    """RN-M03-23: el lloc conserva un centre desactivat i surt marcat fins que es canvia."""
    centre = usual_centre(place)
    return centre is not None and not centre.active


def proposed_centre(place):
    """RN-M03-24 (CA-M03-23): el centre que es proposa en llogar material, si és actiu."""
    centre = usual_centre(place) if place is not None else None
    return centre if centre is not None and centre.active else None
