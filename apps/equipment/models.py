"""Material (mòdul 03; M03-6). Imports en cèntims. Les FK cap al 02 són només de lectura: el 03 no
hi escriu mai. Cap dada personal."""

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


class EquipmentType(models.Model):
    """Tipus de material (T-M03-02; VC-27): una llista ampliable des de l'app. Els 14 inicials de
    F §6 els posa la migració."""

    class Sizing(models.TextChoices):
        SIZE = "size", _("Talla")
        LITRES = "litres", _("Litres")
        NONE = "none", _("Cap")

    name = models.CharField(_("nom"), max_length=60, unique=True)
    sizing = models.CharField(_("mida"), max_length=6, choices=Sizing.choices)
    requires_review = models.BooleanField(_("cal revisió"), default=False)
    active = models.BooleanField(_("actiu"), default=True)

    class Meta:
        verbose_name = _("tipus de material")
        verbose_name_plural = _("tipus de material")
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(sizing__in=["size", "litres", "none"]), name="equipment_type_sizing"
            ),
            models.CheckConstraint(condition=~Q(name=""), name="equipment_type_name"),
        ]

    def __str__(self):
        return self.name
