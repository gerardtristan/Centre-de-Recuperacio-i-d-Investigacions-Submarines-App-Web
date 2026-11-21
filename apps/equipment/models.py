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


class DiveCentre(models.Model):
    """Centre de busseig (T-M03-05; VC-27). Amb tarifes, assignacions o com a centre habitual
    d'un lloc no s'esborra: es desactiva (RN-M03-26 a). Només dades del centre, no de persones."""

    name = models.CharField(_("nom"), max_length=120, unique=True)
    address = models.CharField(_("adreça"), max_length=200, blank=True)
    contact_email = models.EmailField(_("correu del centre"), blank=True)
    contact_phone = models.CharField(_("telèfon del centre"), max_length=30, blank=True)
    active = models.BooleanField(_("actiu"), default=True)
    created_at = models.DateTimeField(_("creat"), auto_now_add=True)

    class Meta:
        verbose_name = _("centre de busseig")
        verbose_name_plural = _("centres de busseig")
        ordering = ["name"]
        constraints = [models.CheckConstraint(condition=~Q(name=""), name="dive_centre_name")]

    def __str__(self):
        return self.name


class CentreRate(models.Model):
    """Tarifa d'un centre amb versions (RN-M03-06): un canvi crea una versió nova amb data
    d'inici, i la que ja s'ha fet servir no es modifica. `retired_on` retira la línia sense
    cap versió nova (RN-M03-26 b)."""

    centre = models.ForeignKey(
        DiveCentre, on_delete=models.PROTECT, related_name="rates", verbose_name=_("centre")
    )
    label = models.CharField(_("equip o servei"), max_length=80)
    equipment_type = models.ForeignKey(
        EquipmentType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("tipus de material"),
    )
    cost_cents = models.PositiveIntegerField(_("preu de cost (cèntims)"))
    member_price_cents = models.PositiveIntegerField(_("preu per al soci (cèntims)"))
    # [A validar: junta, S-M03-01]
    non_member_price_cents = models.PositiveIntegerField(
        _("preu per al no soci (cèntims)"), null=True, blank=True
    )
    valid_from = models.DateField(_("vigent des de"))
    superseded_by = models.OneToOneField(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="supersedes",
        verbose_name=_("substituïda per"),
    )
    retired_on = models.DateField(_("retirada el"), null=True, blank=True)
    note = models.TextField(_("nota"), blank=True)
    created_by = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, related_name="+", verbose_name=_("creada per")
    )
    created_at = models.DateTimeField(_("creada"), auto_now_add=True)

    class Meta:
        verbose_name = _("tarifa d'un centre")
        verbose_name_plural = _("tarifes dels centres")
        ordering = ["centre", "label", "valid_from", "pk"]
        constraints = [
            models.CheckConstraint(condition=~Q(label=""), name="centre_rate_label"),
            models.CheckConstraint(
                condition=Q(retired_on__isnull=True) | Q(retired_on__gte=models.F("valid_from")),
                name="centre_rate_retired_after_start",
            ),
        ]

    def __str__(self):
        return f"{self.centre}: {self.label} ({self.valid_from})"


class PlaceUsualCentre(models.Model):
    """Centre habitual d'un lloc del 02 (T-M03-26; RN-M03-23): una fila per lloc com a màxim.
    El 03 no escriu mai al lloc; cada canvi va al registre amb el valor anterior."""

    place = models.OneToOneField(
        "activities.Place",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("lloc"),
    )
    centre = models.ForeignKey(
        DiveCentre, on_delete=models.PROTECT, related_name="+", verbose_name=_("centre habitual")
    )
    changed_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("canviat per"),
    )
    changed_at = models.DateTimeField(_("canviat"), auto_now=True)

    class Meta:
        verbose_name = _("centre habitual d'un lloc")
        verbose_name_plural = _("centres habituals dels llocs")

    def __str__(self):
        return f"{self.place_id}: {self.centre}"
