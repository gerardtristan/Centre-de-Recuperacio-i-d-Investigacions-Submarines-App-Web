"""Fotos d'una sortida de medi ambient (T-M02-20; M02-6, M02-12; RN-M02-23; CA-M02-22).

La P-41 (autor, permís d'ús i drets d'imatge, junta) és oberta: per D2 és irreversible (imatges
de persones) i aquí hi ha l'opció **més conservadora**, darrere de l'interruptor
`activities.environment_photos_enabled`, **apagat**:
- **Qui:** AC14 per pujar, marcar i retirar; amb «Cons.» (la junta), només veure.
- **Què:** JPEG o PNG (`core.validate_upload`), sense metadades (EXIF, XMP, IPTC, comentaris i
  text del PNG; `card_photos.strip_*`), amb l'autor i el permís d'ús de l'autor obligatoris.
- **Com es desa:** xifrada a l'aplicació (`core.files`, tipus `environment_photo`, la clau que ja
  hi ha), mai amb adreça pública. Només l'obre la vista de fitxers amb AC14, amb registre, i
  amb l'interruptor encès; una foto retirada ja no s'obre.
- **Ús intern:** cap pantalla no la publica (RN-M02-23). `mark_publishable` només desa que
  compleix CA-M02-22 per quan el 07 en pugui publicar (P-41).
- **Retirar** amb motiu: la fila i el fitxer es queden (traça), però no surt ni s'obre.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext as _

from apps.core import audit, business_settings, files
from apps.core.models import PrivateFile

from . import environment, permissions
from .card_photos import strip_jpeg, strip_png
from .models import EnvironmentalPhoto

SWITCH = "activities.environment_photos_enabled"
UPLOADED = "activities.environment_photo.uploaded"
MARKED = "activities.environment_photo.publishable"
RETIRED = "activities.environment_photo.retired"
PHOTO_TYPES = frozenset({"image/jpeg", "image/png"})
_STRIP = {"image/jpeg": strip_jpeg, "image/png": strip_png}
_EXTENSION = {"image/jpeg": "jpg", "image/png": "png"}


def enabled(file=None) -> bool:
    """Apagat, cap foto no es puja ni s'obre, tampoc per l'adreça directa (`files.can_access`)."""
    if not business_settings.get(SWITCH):
        return False
    if file is None:
        return True
    return EnvironmentalPhoto.objects.filter(
        file=file, status=EnvironmentalPhoto.Status.ACTIVE
    ).exists()


def photos_for(activity):
    """Les fotos actives de la sortida (cap, si no té resultats)."""
    return EnvironmentalPhoto.objects.filter(
        result__activity=activity, status=EnvironmentalPhoto.Status.ACTIVE
    ).select_related("file")


@transaction.atomic
def upload(
    activity, uploaded, *, by, author, usage_permission, shows_people=False, people_consent=False,
    request=None,
) -> EnvironmentalPhoto:  # fmt: skip
    permissions.require(by, permissions.ENVIRONMENT)
    if not enabled():
        raise ValidationError(_("Ara mateix no es poden pujar fotos de les sortides."))
    result = environment.results_for(activity)
    if result is None:
        raise ValidationError(_("Primer cal registrar els resultats de la sortida."))
    author = (author or "").strip()
    if not author or not usage_permission:
        raise ValidationError(_("Cal l'autor de la foto i el seu permís d'ús."))
    content_type = files.validate_upload(uploaded, allowed=PHOTO_TYPES)
    uploaded.seek(0)
    content = _STRIP[content_type](uploaded.read())
    file = files.store(
        content, owner=by.person, kind=PrivateFile.Kind.ENVIRONMENT_PHOTO,
        content_type=content_type,
        download_name=f"sortida-{activity.pk}-foto.{_EXTENSION[content_type]}",
    )  # fmt: skip
    photo = EnvironmentalPhoto.objects.create(
        result=result, file=file, content_type=content_type, author=author[:120],
        usage_permission=True, shows_people=bool(shows_people),
        people_consent=bool(shows_people and people_consent), uploaded_by=by,
    )  # fmt: skip
    audit.record(UPLOADED, actor=by, target=photo, details={"activity": activity.pk},
                 request=request)  # fmt: skip
    return photo


def _locked(photo, by):
    permissions.require(by, permissions.ENVIRONMENT)
    return EnvironmentalPhoto.objects.select_for_update().get(pk=photo.pk)


@transaction.atomic
def mark_publishable(photo, *, by, request=None) -> EnvironmentalPhoto:
    """CA-M02-22: sense autor, sense permís o amb persones sense consentiment, es rebutja."""
    photo = _locked(photo, by)
    if photo.status != EnvironmentalPhoto.Status.ACTIVE:
        raise ValidationError(_("Aquesta foto està retirada."))
    if not (photo.author.strip() and photo.usage_permission):
        raise ValidationError(_("Cal l'autor de la foto i el seu permís d'ús."))
    if photo.shows_people and not photo.people_consent:
        raise ValidationError(_("Hi surten persones i no hi ha el seu consentiment."))
    if not photo.publishable:
        photo.publishable = True
        photo.save(update_fields=["publishable"])
        audit.record(MARKED, actor=by, target=photo, field="publishable", old=False, new=True,
                     request=request)  # fmt: skip
    return photo


@transaction.atomic
def retire(photo, *, by, reason: str, request=None) -> EnvironmentalPhoto:
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(_("Cal el motiu de la retirada."))
    photo = _locked(photo, by)
    if photo.status == EnvironmentalPhoto.Status.RETIRED:
        return photo
    photo.status, photo.retired_reason, photo.publishable = (
        EnvironmentalPhoto.Status.RETIRED, reason, False,
    )  # fmt: skip
    photo.save(update_fields=["status", "retired_reason", "publishable"])
    audit.record(RETIRED, actor=by, target=photo, field="status",
                 old=EnvironmentalPhoto.Status.ACTIVE, new=photo.status, reason=reason,
                 request=request)  # fmt: skip
    return photo
