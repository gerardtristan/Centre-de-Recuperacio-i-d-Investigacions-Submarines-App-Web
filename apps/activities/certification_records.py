"""Titulacions inicials: carregar-les a mà i verificar-les (T-M02-52, part de la T-M02-31;
RN-M02-32; AC29, P-459 i decisió 105).

- `load`: la secretaria, el responsable de cursos i sortides o l'administrador (AC29 amb «Sí»)
  carreguen una titulació d'una persona amb origen `declared` o `imported`, sense verificar.
  L'agència d'un nivell és la del nivell; la d'una especialitat, la que es doni.
- `verify`: els mateixos la verifiquen; queda qui i quan. Una de verificada no canvia. Només es
  verifiquen les declarades o importades: les del club i les de la federació ja ho són per origen.

La Junta té AC29 de només consulta: no en carrega ni en verifica cap. Sense el permís, «no
trobat». Ningú no carrega ni verifica les seves pròpies titulacions (conflicte d'interès, com a
la fitxa del soci, S-M01-22). Tot queda al registre d'activitat, només amb identificadors (cap
nom ni número). La importació des de Cluber continua esperant la mostra (Q-23). La pantalla és
`views/admin_certifications.py` (T-M02-52b).
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit

from . import permissions
from .models import CertificationLevel, DiverCertification, TrainingCatalogueEntry

S = DiverCertification.Source
LOADED = "activities.certification.loaded"
VERIFIED = "activities.certification.verified"
MANUAL_SOURCES = (S.DECLARED, S.IMPORTED)


def _require(by, person_id, request) -> None:
    permissions.require(by, permissions.CERTIFICATIONS, request=request)
    if getattr(by, "person_id", None) == person_id:
        raise ValidationError(_("No pots carregar ni verificar les teves pròpies titulacions."))


def load(
    person, *, by, source, level=None, speciality=None, agency=None, number="", issued_on=None,
    request=None,
) -> DiverCertification:  # fmt: skip
    """RN-M02-32: una titulació carregada a mà queda sense verificar."""
    _require(by, person.pk, request)
    if source not in MANUAL_SOURCES:
        raise ValidationError(_("Una titulació carregada a mà és declarada o importada."))
    if (level is None) == (speciality is None):
        raise ValidationError(_("Cal un nivell o una especialitat, només un dels dos."))
    if level is not None and not isinstance(level, CertificationLevel):
        raise ValidationError(_("El nivell no és vàlid."))
    if speciality is not None and (
        not isinstance(speciality, TrainingCatalogueEntry) or speciality.kind != "speciality"
    ):
        raise ValidationError(_("L'especialitat no és vàlida."))
    number = (number or "").strip()
    if len(number) > 40:
        raise ValidationError(_("El número té 40 caràcters com a màxim."))
    certification = DiverCertification.objects.create(
        person=person, level=level, speciality=speciality, number=number, issued_on=issued_on,
        source=source, agency=level.agency if level is not None else agency,
    )  # fmt: skip
    audit.record(
        LOADED, actor=by, target=certification, details={"source": source}, request=request
    )
    return certification


@transaction.atomic
def verify(certification, *, by, now=None, request=None) -> DiverCertification:
    """RN-M02-32: qui i quan. Idempotent: una de verificada es torna tal com és."""
    _require(by, certification.person_id, request)
    locked = DiverCertification.objects.select_for_update().get(pk=certification.pk)
    if locked.is_verified:
        return locked
    if locked.source not in MANUAL_SOURCES:
        raise ValidationError(_("Només es verifiquen les titulacions declarades o importades."))
    locked.verified_by, locked.verified_at = by, now or timezone.now()
    locked.save(update_fields=["verified_by", "verified_at"])
    audit.record(VERIFIED, actor=by, target=locked, request=request)
    return locked
