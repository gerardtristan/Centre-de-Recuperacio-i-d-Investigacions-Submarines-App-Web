"""Pujar la foto del carnet d'una titulació (T-M02-42b; addenda de la 104; RN-M02-47 i 56;
CA-M02-52). Les regles són al servei (`card_photos.upload`), que ho torna a comprovar tot.

- **Àrea personal** (`/socis/titulacions/<id>/foto/`): el titular, només per a les seves
  titulacions (una d'una altra persona: «no trobat»).
- **Administració** (`homologacions/titulacions/<id>/foto/`): qui té AC25, en nom de la persona.
- **Amb VC-56 apagat, cap de les dues pantalles existeix** («no trobat») i cap enllaç hi porta.
- L'avís de RN-M02-47 diu per a què serveix, quant temps es conserva (VC-57) i que no s'hi pugi
  cap document de salut. Es diu quines cares ja tenen foto, però la foto no es mostra (T-M02-43).
"""

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.core import business_settings
from apps.core.permissions import permission_required

from .. import card_photos
from ..filings import PHOTOS_KEY
from ..models import CertificationCardPhoto, DiverCertification
from ..permissions import CARD_PHOTOS_MANAGE
from . import see_other
from .member_certifications import _person

RETENTION_KEY = "activities.card_photo_retention_months"  # VC-57


class PhotoForm(forms.Form):
    side = forms.ChoiceField(
        label=_("Cara del carnet"), choices=CertificationCardPhoto.Side.choices
    )
    photo = forms.FileField(
        label=_("Foto o PDF"),
        help_text=_("Una foto (JPEG o PNG) o un PDF. Es desa sense les dades amagades de la foto."),
        widget=forms.FileInput(attrs={"accept": ".jpg,.jpeg,.png,.pdf"}),
    )


def enabled() -> bool:
    return bool(business_settings.get(PHOTOS_KEY))


def _page(request, cert, *, template, done, file_route):
    if not enabled():
        raise Http404
    form = PhotoForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        try:
            card_photos.upload(cert, data["side"], data["photo"], by=request.user, request=request)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(
                request, _("Foto desada, xifrada: només la veuen el titular i la secretaria.")
            )
            return see_other(*done)
    context = {
        "cert": cert,
        "form": form,
        "sides": cert.card_photos.order_by("-side"),  # l'anvers primer
        "months": business_settings.get(RETENTION_KEY),
        "file_route": file_route,  # la vista que desxifra amb permís i registre (T-M02-43)
    }
    return render(request, template, context)


@never_cache
@require_http_methods(["GET", "POST"])
def my_photo_view(request, pk):
    cert = get_object_or_404(DiverCertification, pk=pk, person=_person(request))
    return _page(
        request, cert, template="activities/my_card_photo.html",
        done=("activities:my_certifications",), file_route="core:private_file",
    )  # fmt: skip


@never_cache
@permission_required(CARD_PHOTOS_MANAGE, write=True)
@require_http_methods(["GET", "POST"])
def admin_photo_view(request, pk):
    cert = get_object_or_404(DiverCertification.objects.select_related("person"), pk=pk)
    return _page(
        request, cert, template="activities/admin_card_photo.html",
        done=("administration:certification_photo", cert.pk),
        file_route="administration:private_file",
    )  # fmt: skip
