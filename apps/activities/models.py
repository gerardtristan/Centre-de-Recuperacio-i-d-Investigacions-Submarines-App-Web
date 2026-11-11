"""Models del mòdul 02, Activitats (cursos i sortides). Primera peça: catàlegs, tipus, subtipus,
projectes i preus amb versions (T-M02-02; pla, M02-6; RN-M02-01 i RN-M02-05; VC-20).

- Imports en cèntims (enters, ≥ 0: una activitat pot ser gratuïta, L-M02-06).
- Cap dada de salut, de targeta ni d'IBAN (CA-M02-25).
- Les fitxes, els tipus i els projectes no s'esborren quan tinguin activitats (PROTECT des de
  `Activity`, T-M02-03): es desactiven.
- Els estats i els preus només canvien amb els serveis d'`apps.activities.catalogue`.

`Activity`, `Session`, `ProgrammeBlock` i la resta són de les tasques següents (T-M02-03 i
posteriors) i encara no existeixen.
"""

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.core.models import AppendOnlyModel, Department


class TrainingCatalogueEntry(models.Model):
    """Fitxa del catàleg de cursos o del d'especialitats: dos catàlegs separats (RN-M02-01)."""

    class Kind(models.TextChoices):
        COURSE = "course", _("Curs")
        SPECIALITY = "speciality", _("Especialitat")

    kind = models.CharField(_("catàleg"), max_length=10, choices=Kind.choices)
    name = models.CharField(_("nom"), max_length=120)
    # Nivell que dona o requereix [A verificar: FECDAS]; la llista de nivells és de la T-M02-29.
    level = models.CharField(_("nivell"), max_length=60, blank=True)
    description = models.TextField(_("descripció"), blank=True)
    requirements = models.TextField(_("requisits"), blank=True)
    default_places = models.PositiveSmallIntegerField(_("places per defecte"))
    # Preu inicial de la fitxa. El preu vigent en una data surt de les versions
    # (`TrainingCataloguePrice`, `catalogue.price_on`): aquests camps no es toquen en canviar-lo.
    price_member_cents = models.PositiveIntegerField(_("preu de soci (cèntims)"))
    price_non_member_cents = models.PositiveIntegerField(_("preu de no soci (cèntims)"))
    # Preu d'una classe de reforç [A validar: junta, S-M02-08].
    reinforcement_price_cents = models.PositiveIntegerField(
        _("preu del reforç (cèntims)"), null=True, blank=True
    )
    open_to_non_members = models.BooleanField(_("oberta a no socis"), default=False)
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("departament"),
    )
    active = models.BooleanField(_("activa"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("fitxa del catàleg")
        verbose_name_plural = _("fitxes del catàleg")
        ordering = ["kind", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "name"], name="trainingcatalogueentry_name_unique_per_kind"
            ),
            models.CheckConstraint(
                condition=Q(kind__in=["course", "speciality"]),
                name="trainingcatalogueentry_kind_valid",
            ),
            models.CheckConstraint(
                condition=Q(default_places__gt=0), name="trainingcatalogueentry_places_positive"
            ),
        ]

    def __str__(self):
        return self.name


class TrainingCataloguePrice(AppendOnlyModel):
    """Versió dels preus d'una fitxa amb data d'entrada en vigor (RN-M02-05, VC-20). Només s'hi
    afegeixen files: una correcció és una versió nova."""

    entry = models.ForeignKey(
        TrainingCatalogueEntry,
        on_delete=models.PROTECT,
        related_name="prices",
        verbose_name=_("fitxa"),
    )
    price_member_cents = models.PositiveIntegerField(_("preu de soci (cèntims)"))
    price_non_member_cents = models.PositiveIntegerField(_("preu de no soci (cèntims)"))
    reinforcement_price_cents = models.PositiveIntegerField(
        _("preu del reforç (cèntims)"), null=True, blank=True
    )
    valid_from = models.DateField(_("vigent des del"))
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("canviat per"),
    )
    note = models.TextField(_("motiu"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("preu del catàleg")
        verbose_name_plural = _("preus del catàleg")
        indexes = [
            models.Index(fields=["entry", "valid_from"], name="cataloguepriceentry_from_idx")
        ]

    def __str__(self):
        return f"{self.entry} ({self.valid_from:%d/%m/%Y})"


class OutingType(models.Model):
    """Tipus de sortida. Els de medi ambient admeten subtipus i projecte."""

    name = models.CharField(_("nom"), max_length=80, unique=True)
    is_environmental = models.BooleanField(_("és de medi ambient"), default=False)
    default_department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("departament per defecte"),
    )
    active = models.BooleanField(_("actiu"), default=True)

    class Meta:
        verbose_name = _("tipus de sortida")
        verbose_name_plural = _("tipus de sortida")
        ordering = ["name"]

    def __str__(self):
        return self.name


class EnvironmentalSubtype(models.Model):
    """Subtipus d'una sortida de medi ambient (ampliable pel responsable)."""

    name = models.CharField(_("nom"), max_length=80, unique=True)
    active = models.BooleanField(_("actiu"), default=True)

    class Meta:
        verbose_name = _("subtipus de medi ambient")
        verbose_name_plural = _("subtipus de medi ambient")
        ordering = ["name"]

    def __str__(self):
        return self.name


class EnvironmentalProject(models.Model):
    """Projecte de medi ambient: acumula els resultats de les seves sortides (T-M02-20)."""

    class Status(models.TextChoices):
        ACTIVE = "active", _("Actiu")
        FINISHED = "finished", _("Acabat")

    name = models.CharField(_("nom"), max_length=120, unique=True)
    objective = models.TextField(_("objectiu"))
    status = models.CharField(
        _("estat"), max_length=10, choices=Status.choices, default=Status.ACTIVE
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("departament"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("projecte de medi ambient")
        verbose_name_plural = _("projectes de medi ambient")
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=["active", "finished"]),
                name="environmentalproject_status_valid",
            ),
        ]

    def __str__(self):
        return self.name
