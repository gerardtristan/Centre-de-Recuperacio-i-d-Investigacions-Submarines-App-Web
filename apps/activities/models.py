"""Models del mòdul 02, Activitats (cursos i sortides).

- **Catàleg** (T-M02-02; M02-6; RN-M02-01 i RN-M02-05; VC-20): fitxes de cursos i d'especialitats,
  preus amb versions, tipus de sortida, subtipus i projectes.
- **Activitat, sessió i bloc de programa** (T-M02-03; M02-6; RN-M02-02 i RN-M02-20).

Regles comunes:
- Imports en cèntims (enters, ≥ 0: una activitat pot ser gratuïta, L-M02-06).
- Cap dada de salut, de targeta ni d'IBAN (CA-M02-25).
- Les fitxes, els tipus, els subtipus i els projectes no s'esborren si tenen activitats (PROTECT):
  es desactiven.
- Res no es desa directament: el catàleg canvia amb `apps.activities.catalogue`, les activitats amb
  `apps.activities.services`, l'estat amb `apps.activities.states` i les sessions i el programa amb
  `apps.activities.sessions`.

Encara no existeixen, i cap codi no els simula: `Activity.cost_centre` (el centre de cost és de la
04), `Session.reinforcement_for` (la inscripció és de la T-M02-11), els camps de l'addenda de la
058 (`min_level`, especialitats exigides i edat mínima: T-M02-29 i T-M02-32) i la resta d'entitats
(inscripcions, assistència, avaluacions, titulacions i resultats ambientals).
"""

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _

from apps.core.models import AppendOnlyModel, Department, Person


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


class Activity(models.Model):
    """Una activitat: un curs (d'una fitxa del catàleg) o una sortida (d'un tipus). L'estat només
    canvia amb `apps.activities.states` (RN-M02-02)."""

    class Kind(models.TextChoices):
        COURSE = "course", _("Curs")
        OUTING = "outing", _("Sortida")
        # `conference` s'hi afegirà amb el mòdul 11.

    class Status(models.TextChoices):
        DRAFT = "draft", _("Esborrany")
        OPEN = "open", _("Oberta")
        REGISTRATION_CLOSED = "registration_closed", _("Tancada a inscripcions")
        IN_PROGRESS = "in_progress", _("En curs")
        DONE = "done", _("Finalitzada")
        CLOSED = "closed", _("Tancada econòmicament")
        CANCELLED = "cancelled", _("Cancel·lada")

    class RequirementsMode(models.TextChoices):
        WARN = "warn", _("Avís")
        BLOCK = "block", _("Bloqueig")

    kind = models.CharField(_("classe"), max_length=10, choices=Kind.choices)
    title = models.CharField(_("títol"), max_length=140)
    # Objectiu (sortides) o descripció (cursos).
    description = models.TextField(_("descripció"), blank=True)
    catalogue_entry = models.ForeignKey(
        TrainingCatalogueEntry,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="activities",
        verbose_name=_("fitxa del catàleg"),
    )
    outing_type = models.ForeignKey(
        OutingType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="activities",
        verbose_name=_("tipus de sortida"),
    )
    # Només si el tipus és de medi ambient (`catalogue.check_outing_classification`, CA-M02-03).
    subtype = models.ForeignKey(
        EnvironmentalSubtype,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="activities",
        verbose_name=_("subtipus"),
    )
    project = models.ForeignKey(
        EnvironmentalProject,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="activities",
        verbose_name=_("projecte"),
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("departament"),
    )
    status = models.CharField(
        _("estat"), max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    starts_on = models.DateField(_("data d'inici"))
    ends_on = models.DateField(_("data de final"))
    location = models.CharField(_("lloc"), max_length=140, blank=True)
    meeting_point = models.CharField(_("punt de trobada"), max_length=140, blank=True)
    max_places = models.PositiveSmallIntegerField(_("places"))
    registration_closes_at = models.DateTimeField(_("data límit d'inscripció"))
    payment_window_hours = models.PositiveSmallIntegerField(_("termini de pagament (hores)"))
    # Còpia del preu vigent del catàleg el dia que es crea (RN-M02-05); a les sortides, el que
    # escriu el responsable. Canviar el catàleg no els toca mai.
    price_member_cents = models.PositiveIntegerField(_("preu de soci (cèntims)"))
    price_non_member_cents = models.PositiveIntegerField(_("preu de no soci (cèntims)"))
    # Obligatori si algun preu difereix del catàleg (RN-M02-06; validació de servei).
    price_override_note = models.TextField(_("motiu del preu diferent del catàleg"), blank=True)
    open_to_non_members = models.BooleanField(_("oberta a no socis"), default=False)
    required_level = models.CharField(_("titulació mínima"), max_length=60, blank=True)
    licence_required = models.BooleanField(_("cal llicència vigent"), default=False)
    requirements_mode = models.CharField(
        _("si no es compleixen els requisits"),
        max_length=5,
        choices=RequirementsMode.choices,
        default=RequirementsMode.WARN,
    )
    responsible = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("persona responsable"),
    )
    # Només un enllaç a la previsió marítima, mai un giny ni un script (RN-M02-24).
    forecast_url = models.URLField(_("enllaç a la previsió marítima"), blank=True)
    duplicated_from = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="copies",
        verbose_name=_("duplicada de"),
    )
    cancellation_reason = models.TextField(_("motiu de la cancel·lació"), blank=True)
    published_at = models.DateTimeField(_("publicada el"), null=True, blank=True)
    done_at = models.DateTimeField(_("finalitzada el"), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("activitat")
        verbose_name_plural = _("activitats")
        ordering = ["starts_on", "pk"]
        indexes = [
            models.Index(fields=["status", "starts_on"], name="activity_status_start_idx"),
            models.Index(fields=["kind", "starts_on"], name="activity_kind_start_idx"),
            models.Index(fields=["project"], name="activity_project_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(kind__in=["course", "outing"]), name="activity_kind_valid"
            ),
            models.CheckConstraint(
                condition=Q(
                    status__in=[
                        "draft",
                        "open",
                        "registration_closed",
                        "in_progress",
                        "done",
                        "closed",
                        "cancelled",
                    ]
                ),
                name="activity_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(requirements_mode__in=["warn", "block"]),
                name="activity_requirements_mode_valid",
            ),
            models.CheckConstraint(
                condition=~Q(kind="course") | Q(catalogue_entry__isnull=False),
                name="activity_course_has_catalogue_entry",
            ),
            models.CheckConstraint(
                condition=~Q(kind="outing") | Q(outing_type__isnull=False),
                name="activity_outing_has_type",
            ),
            models.CheckConstraint(
                condition=Q(ends_on__gte=F("starts_on")), name="activity_ends_after_it_starts"
            ),
            models.CheckConstraint(condition=Q(max_places__gt=0), name="activity_places_positive"),
            models.CheckConstraint(
                condition=~Q(status="cancelled") | ~Q(cancellation_reason=""),
                name="activity_cancelled_has_reason",
            ),
        ]

    def __str__(self):
        return self.title


class Session(models.Model):
    """Sessió d'un curs: teoria, piscina o mar, amb els instructors que hi fan classe. «Les seves
    sessions» d'un instructor (RN-43 de la 00) són aquelles on surt a `instructors`."""

    class Kind(models.TextChoices):
        THEORY = "theory", _("Teoria")
        POOL = "pool", _("Piscina")
        SEA = "sea", _("Mar")

    activity = models.ForeignKey(
        Activity, on_delete=models.PROTECT, related_name="sessions", verbose_name=_("activitat")
    )
    kind = models.CharField(_("classe"), max_length=10, choices=Kind.choices)
    starts_at = models.DateTimeField(_("comença"))
    ends_at = models.DateTimeField(_("acaba"))
    location = models.CharField(_("lloc"), max_length=140, blank=True)
    instructors = models.ManyToManyField(
        Person, blank=True, related_name="taught_sessions", verbose_name=_("instructors")
    )
    is_practice = models.BooleanField(_("és una pràctica"), default=False)
    cancelled = models.BooleanField(_("cancel·lada"), default=False)
    cancellation_reason = models.TextField(_("motiu de la cancel·lació"), blank=True)

    class Meta:
        verbose_name = _("sessió")
        verbose_name_plural = _("sessions")
        ordering = ["starts_at", "pk"]
        indexes = [
            models.Index(fields=["activity", "starts_at"], name="session_activity_start_idx")
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(kind__in=["theory", "pool", "sea"]), name="session_kind_valid"
            ),
            models.CheckConstraint(
                condition=Q(ends_at__gt=F("starts_at")), name="session_ends_after_it_starts"
            ),
            models.CheckConstraint(
                condition=Q(cancelled=False) | ~Q(cancellation_reason=""),
                name="session_cancelled_has_reason",
            ),
        ]

    def __str__(self):
        return f"{self.activity} ({self.starts_at:%d/%m/%Y %H:%M})"


class ProgrammeBlock(models.Model):
    """Bloc del programa del dia d'una sortida (trobada, briefing, immersió, dinar, tornada)."""

    activity = models.ForeignKey(
        Activity,
        on_delete=models.PROTECT,
        related_name="programme_blocks",
        verbose_name=_("activitat"),
    )
    order = models.PositiveSmallIntegerField(_("ordre"))
    starts_at = models.TimeField(_("hora d'inici"))
    ends_at = models.TimeField(_("hora de final"), null=True, blank=True)
    label = models.CharField(_("què s'hi fa"), max_length=80)
    location = models.CharField(_("lloc"), max_length=140, blank=True)
    # Rol o funció («cap d'immersió»), mai un nom ni dades de contacte.
    responsible_label = models.CharField(
        _("qui se n'encarrega (funció)"), max_length=80, blank=True
    )

    class Meta:
        verbose_name = _("bloc del programa")
        verbose_name_plural = _("blocs del programa")
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["activity", "order"], name="programmeblock_order_unique_per_activity"
            ),
        ]

    def __str__(self):
        return f"{self.starts_at:%H:%M} {self.label}"
