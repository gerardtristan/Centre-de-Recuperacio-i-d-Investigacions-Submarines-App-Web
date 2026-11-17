"""Navegació de l'àrea del soci (T-DX-45): si surt l'entrada «Mandat de domiciliació». Amagar
l'enllaç no és cap control: la vista respon «no trobat» amb l'ajust apagat i sense mandat actiu
(T-M05a-09)."""

from django import template
from django.conf import settings

from apps.payments.models import SepaMandate

register = template.Library()


@register.simple_tag(takes_context=True)
def mandate_signing_enabled(context):
    """Amb la signatura encesa, sí. Apagada, només a qui té un mandat actiu, perquè revocar
    funciona sempre (P-127, decisió 095). El nom es manté: el fan servir les plantilles de
    navegació, que són del carril de disseny."""
    if settings.MANDATE_SIGNING_ENABLED:
        return True
    person_id = getattr(context["request"].user, "person_id", None)
    return SepaMandate.objects.filter(
        member__person_id=person_id, status=SepaMandate.Status.ACTIVE
    ).exists()
