"""Necessitats de material a la inscripció (T-M03-07; P-M03-C; HU-M03-04; MT1).

El bloc es registra al 02 (`extensions.register_enrolment_section`) des del `ready()` del 03: el
formulari d'inscripció pregunta, per a cada tipus del material típic de l'activitat, «porto el
meu» o «necessito» i la talla (o els litres). El 02 desa les respostes ja validades dins la
transacció de la inscripció cridant `section_save`; també d'una inscripció a la llista d'espera.

- La talla (o els litres) només cal quan es necessita la peça: és el que farà servir l'assignació
  (T-M03-08). Si es porta la pròpia, es pot donar però no s'exigeix.
- Una resposta d'un tipus que no és al material típic de l'activitat es rebutja.
- Són dades de la persona (talles): les veuen ella mateixa, el responsable de material i, per a les
  seves sessions, l'instructor (M03-4). Cap dada de salut.

**Fora d'aquesta peça:** canviar les necessitats després d'inscriure's i el RGPD del 03 (L-M03-07).
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .measures import clean_measure
from .models import EquipmentNeed, EquipmentType
from .typical import lines_for

SECTION_KEY = "equipment.needs"
OWN, NEED = "own", "need"
CHOICES = ((OWN, _("Porto el meu")), (NEED, _("Necessito")))


def section_fields(activity, person=None) -> dict:
    """Camps del bloc del 03: per a cada tipus, la tria i la mida que porta el tipus."""
    fields = {}
    for equipment_type, _quantity in lines_for(activity):
        pk = equipment_type.pk
        fields[f"need_{pk}"] = forms.ChoiceField(
            label=equipment_type.name, choices=CHOICES, widget=forms.RadioSelect
        )
        if equipment_type.sizing == EquipmentType.Sizing.SIZE:
            fields[f"size_{pk}"] = forms.CharField(label=_("Talla"), max_length=10, required=False)
        elif equipment_type.sizing == EquipmentType.Sizing.LITRES:
            fields[f"litres_{pk}"] = forms.DecimalField(
                label=_("Litres"), max_digits=4, decimal_places=1, required=False
            )
    return fields


def _answers(activity, data: dict) -> list[EquipmentNeed]:
    types = {t.pk: t for t, _quantity in lines_for(activity)}
    needs = []
    for key, choice in data.items():
        if not key.startswith("need_"):
            continue
        equipment_type = types.get(int(key.removeprefix("need_")))
        if equipment_type is None:
            raise ValidationError(_("Aquest material no és de l'activitat."))
        if choice not in (OWN, NEED):
            raise ValidationError(_("Cal dir si el portes o el necessites."))
        size = data.get(f"size_{equipment_type.pk}") or ""
        litres = data.get(f"litres_{equipment_type.pk}")
        brings_own = choice == OWN
        if not brings_own or size or litres is not None:
            size, litres = clean_measure(equipment_type, size, litres)
        needs.append(
            EquipmentNeed(
                equipment_type=equipment_type, brings_own=brings_own, size=size, litres=litres
            )
        )
    return needs


def section_save(enrolment, data: dict) -> list[EquipmentNeed]:
    """Desa les necessitats de la inscripció. Torna a escriure-les totes si ja n'hi havia."""
    needs = _answers(enrolment.activity, data)
    EquipmentNeed.objects.filter(enrolment=enrolment).delete()
    for need in needs:
        need.enrolment = enrolment
    return EquipmentNeed.objects.bulk_create(needs)


def needs_of(activity):
    """Les necessitats de les inscripcions de l'activitat, per al material de l'activitat."""
    return (
        EquipmentNeed.objects.filter(enrolment__activity=activity)
        .select_related("equipment_type", "enrolment")
        .order_by("enrolment_id", "equipment_type__name")
    )
