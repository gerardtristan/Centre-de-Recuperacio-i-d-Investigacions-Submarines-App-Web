"""Models del mòdul 02, Activitats (cursos i sortides). Primera peça: catàlegs, tipus, subtipus,
projectes i preus amb versions (T-M02-02; M02-6; RN-M02-01 i RN-M02-05; VC-20), i llocs amb el
seu preu estàndard (T-M02-37; addenda de llocs; RN-M02-38 i 39; VC-52). Activitats, sessions i
blocs del programa (T-M02-03a; M02-6). Nivells i titulacions (T-M02-23; addenda de la 058).

- Imports en cèntims (enters, ≥ 0: una activitat pot ser gratuïta, L-M02-06). Cap dada de salut,
  de targeta ni d'IBAN (CA-M02-25).
- Fitxes, tipus, projectes i llocs no s'esborren si tenen activitats (PROTECT): es desactiven. Els
  preus només canvien amb `apps.activities.catalogue`.
"""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _

from apps.core.models import AppendOnlyModel, Department, Person


class RequirementsMode(models.TextChoices):
    """Què passa quan algú no compleix els requisits d'una activitat (RN-M02-10)."""

    WARN = "warn", _("Avís")
    BLOCK = "block", _("Bloqueig")


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
    # Edat mínima que copien les activitats noves (RN-M02-33). Buit: sense edat mínima.
    min_age = models.PositiveSmallIntegerField(_("edat mínima"), null=True, blank=True)
    # Addenda de la 104 (RN-M02-52): el nivell oficial que es tramita a la federació quan
    # l'alumne queda apte (la primera estrella) [A verificar: responsable de cursos i sortides].
    official_level = models.ForeignKey(
        "CertificationLevel", on_delete=models.PROTECT, null=True, blank=True,
        related_name="+", verbose_name=_("nivell oficial que es tramita"),
    )  # fmt: skip
    # Mode de requisits que copien les activitats noves (RN-M02-29). Buit: val l'ajust general.
    default_requirements_mode = models.CharField(
        _("mode de requisits per defecte"),
        max_length=5,
        choices=RequirementsMode.choices,
        blank=True,
        default="",
    )
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
            models.CheckConstraint(
                condition=Q(default_requirements_mode__in=["", "warn", "block"]),
                name="trainingcatalogueentry_default_mode_valid",
            ),
            models.CheckConstraint(
                condition=Q(min_age__isnull=True) | Q(min_age__gte=1, min_age__lte=99),
                name="trainingcatalogueentry_min_age_valid",
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
    # Mode de requisits que copien les activitats noves (RN-M02-29). Buit: val l'ajust general.
    default_requirements_mode = models.CharField(
        _("mode de requisits per defecte"),
        max_length=5,
        choices=RequirementsMode.choices,
        blank=True,
        default="",
    )

    class Meta:
        verbose_name = _("tipus de sortida")
        verbose_name_plural = _("tipus de sortida")
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(default_requirements_mode__in=["", "warn", "block"]),
                name="outingtype_default_mode_valid",
            ),
        ]

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


class Place(models.Model):
    """Lloc d'una activitat: un lloc de sortida, una piscina o l'aula del club (addenda de llocs,
    RN-M02-38). És una dada: es crea, s'edita i es desactiva des de l'app; no s'esborra si té
    activitats, sessions o blocs (PROTECT)."""

    name = models.CharField(_("nom"), max_length=120)
    active = models.BooleanField(_("actiu"), default=True)
    notes = models.TextField(
        _("notes internes"),
        max_length=1000,
        blank=True,
        help_text=_("Sense dades personals ni de salut."),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("creat per"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("lloc")
        verbose_name_plural = _("llocs")
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(Lower("name"), name="place_name_unique_ci"),
        ]

    def __str__(self):
        return self.name


class PlacePrice(AppendOnlyModel):
    """Preu estàndard de la sortida en un lloc, amb data d'entrada en vigor (RN-M02-39). Només
    s'hi afegeixen files, com `TrainingCataloguePrice`. Un lloc sense cap fila no té preu."""

    place = models.ForeignKey(
        Place, on_delete=models.PROTECT, related_name="prices", verbose_name=_("lloc")
    )
    price_member_cents = models.PositiveIntegerField(_("preu de soci (cèntims)"))
    price_non_member_cents = models.PositiveIntegerField(_("preu de no soci (cèntims)"))
    valid_from = models.DateField(_("vigent des del"))
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("canviat per"),
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(_("motiu"))

    class Meta:
        verbose_name = _("preu estàndard del lloc")
        verbose_name_plural = _("preus estàndard dels llocs")
        indexes = [models.Index(fields=["place", "valid_from"], name="placeprice_from_idx")]

    def __str__(self):
        return f"{self.place} ({self.valid_from:%d/%m/%Y})"


class SpecialitiesRule(models.TextChoices):
    """Si calen totes les especialitats exigides o n'hi ha prou amb una (RN-M02-28)."""

    ALL = "all", _("Totes")
    ANY = "any", _("Alguna")


class Activity(models.Model):
    """Una activitat: un curs (d'una fitxa del catàleg) o una sortida (d'un tipus). L'estat només
    canviarà amb els serveis d'estats (RN-M02-02, T-M02-03b)."""

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
    # Del mateix departament (validació de servei, T-M02-06), com `core.Charge.cost_centre`.
    cost_centre = models.ForeignKey(
        "treasury.CostCentre",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("centre de cost"),
    )
    status = models.CharField(
        _("estat"), max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    starts_on = models.DateField(_("data d'inici"))
    ends_on = models.DateField(_("data de final"))
    # Obligatori a les sortides fora de l'esborrany (addenda de llocs; RN-M02-44: una còpia amb un
    # lloc desactivat el deixa buit); opcional als cursos, que el tenen a cada sessió.
    place = models.ForeignKey(
        Place,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="activities",
        verbose_name=_("lloc"),
    )
    # El punt concret de trobada (un moll, una hora): text lliure.
    meeting_point = models.CharField(_("punt de trobada"), max_length=140, blank=True)
    max_places = models.PositiveSmallIntegerField(_("places"))
    registration_closes_at = models.DateTimeField(_("data límit d'inscripció"))
    payment_window_hours = models.PositiveSmallIntegerField(_("termini de pagament (hores)"))
    # Còpia del preu vigent del catàleg el dia que es crea (RN-M02-05); a les sortides, el que
    # escriu el responsable. Canviar el catàleg no els toca mai.
    price_member_cents = models.PositiveIntegerField(_("preu de soci (cèntims)"))
    price_non_member_cents = models.PositiveIntegerField(_("preu de no soci (cèntims)"))
    # Còpia del preu estàndard en crear-la: del lloc (sortides) o del catàleg (cursos); buida si no
    # n'hi havia (RN-M02-40). La nota és obligatòria si un preu en difereix (RN-M02-41, servei).
    standard_price_member_cents = models.PositiveIntegerField(
        _("preu estàndard de soci (cèntims)"), null=True, blank=True
    )
    standard_price_non_member_cents = models.PositiveIntegerField(
        _("preu estàndard de no soci (cèntims)"), null=True, blank=True
    )
    price_override_note = models.TextField(_("motiu del preu diferent de l'estàndard"), blank=True)
    # Cost de material previst per participant i la seva còpia estàndard del 03 (RN-M02-43). És
    # una previsió: no crea cap càrrec. Només el veu qui té C7 (T-M02-38).
    material_cost_cents = models.PositiveIntegerField(
        _("cost de material previst (cèntims)"), null=True, blank=True
    )
    standard_material_cost_cents = models.PositiveIntegerField(
        _("cost de material estàndard (cèntims)"), null=True, blank=True
    )
    material_cost_note = models.TextField(_("motiu del cost de material diferent"), blank=True)
    open_to_non_members = models.BooleanField(_("oberta a no socis"), default=False)
    required_level = models.CharField(_("titulació mínima"), max_length=60, blank=True)
    # Requisits de l'addenda de la 058 (RN-M02-27 i 28): `required_level` queda com a text
    # informatiu; el que es comprova és `min_level` i les especialitats.
    min_level = models.ForeignKey(
        "CertificationLevel",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="activities",
        verbose_name=_("nivell mínim"),
    )
    required_specialities = models.ManyToManyField(
        TrainingCatalogueEntry,
        blank=True,
        limit_choices_to={"kind": "speciality"},
        related_name="required_by",
        verbose_name=_("especialitats exigides"),
    )
    specialities_rule = models.CharField(
        _("especialitats"), max_length=3, choices=SpecialitiesRule.choices, default="all"
    )
    # RN-M02-33: anys complerts el dia d'inici. Buit: sense edat mínima.
    min_age = models.PositiveSmallIntegerField(_("edat mínima"), null=True, blank=True)
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
                condition=Q(specialities_rule__in=["all", "any"]),
                name="activity_specialities_rule_valid",
            ),
            models.CheckConstraint(
                condition=Q(min_age__isnull=True) | Q(min_age__gte=1, min_age__lte=99),
                name="activity_min_age_valid",
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
            models.CheckConstraint(
                condition=~Q(kind="outing") | Q(place__isnull=False) | Q(status="draft"),
                name="activity_outing_has_place",
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
    place = models.ForeignKey(
        Place, on_delete=models.PROTECT, related_name="sessions", verbose_name=_("lloc")
    )
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
    # Buit: el de l'activitat (`shown_place`).
    place = models.ForeignKey(
        Place,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="programme_blocks",
        verbose_name=_("lloc"),
    )
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

    @property
    def shown_place(self):
        """El lloc que es mostra: el del bloc o, si no en té, el de l'activitat (CA-M02-47)."""
        return self.place or self.activity.place


class CertificationAgency(models.Model):
    """Agència o federació que emet titulacions (addenda de la 104; VC-55). És una dada: la
    mantenen els rols amb AC6. Amb titulacions no s'esborra (PROTECT): es desactiva."""

    name = models.CharField(_("nom"), max_length=60, unique=True)
    active = models.BooleanField(_("activa"), default=True)

    class Meta:
        verbose_name = _("agència de titulació")
        verbose_name_plural = _("agències de titulació")
        ordering = ["name"]

    def __str__(self):
        return self.name


class CertificationLevel(models.Model):
    """Nivell de titulació de busseig, amb un ordre: un `rank` més alt és un nivell més alt
    (addenda de la 058; RN-M02-27). La llista la manté el responsable de cursos i sortides; no
    porta dades inicials [A verificar: FECDAS, S-M02-11]."""

    name = models.CharField(_("nom"), max_length=60, unique=True)
    rank = models.PositiveSmallIntegerField(_("ordre"), unique=True)
    agency = models.ForeignKey(
        CertificationAgency, on_delete=models.PROTECT, null=True, blank=True,
        related_name="levels", verbose_name=_("agència o federació"),
    )  # fmt: skip
    active = models.BooleanField(_("actiu"), default=True)

    class Meta:
        verbose_name = _("nivell de titulació")
        verbose_name_plural = _("nivells de titulació")
        ordering = ["rank"]

    def __str__(self):
        return self.name


class DiverCertification(models.Model):
    """Titulació de busseig d'una persona: un nivell o una especialitat (T-M02-23; M02-6 i
    addenda de la 058; RN-M02-10, RN-M02-30 i RN-M02-32). És una dada personal: només la veu qui
    té permís i surt a l'exportació RGPD de la persona. Cap foto ni escaneig del carnet.

    - `source`: `club_course` (un curs del club), `declared` (ho diu la persona) o `imported`.
    - Verificada: `verified_by` i `verified_at` informats. En mode de bloqueig només compten les
      verificades i les del club (RN-M02-30)."""

    class Source(models.TextChoices):
        CLUB_COURSE = "club_course", _("Curs del club")
        DECLARED = "declared", _("Declarada")
        IMPORTED = "imported", _("Importada")
        # Addenda de la 104: creada en tancar una tramitació a la federació.
        FEDERATION = "federation", _("Tramitada a la federació")

    person = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,
        related_name="diver_certifications",
        verbose_name=_("persona"),
    )
    level = models.ForeignKey(
        CertificationLevel,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="certifications",
        verbose_name=_("nivell"),
    )
    speciality = models.ForeignKey(
        TrainingCatalogueEntry,
        on_delete=models.PROTECT,
        limit_choices_to={"kind": "speciality"},
        null=True,
        blank=True,
        related_name="certifications",
        verbose_name=_("especialitat"),
    )
    agency = models.ForeignKey(
        CertificationAgency, on_delete=models.PROTECT, null=True, blank=True,
        related_name="certifications", verbose_name=_("agència o federació"),
    )  # fmt: skip
    issuer = models.CharField(_("qui l'ha emesa"), max_length=120, blank=True)
    number = models.CharField(_("número de la titulació"), max_length=40, blank=True)
    certificate_number = models.CharField(_("número del certificat"), max_length=40, blank=True)
    issued_on = models.DateField(_("data"), null=True, blank=True)
    source = models.CharField(_("origen"), max_length=12, choices=Source.choices)
    instructor = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("instructor"),
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("verificada per"),
    )
    verified_at = models.DateTimeField(_("verificada el"), null=True, blank=True)
    # RN-M02-31: la titulació del club queda lligada al resultat del curs que la dona.
    course_outcome = models.ForeignKey(
        "CourseOutcome", on_delete=models.PROTECT, null=True, blank=True, related_name="+",
        verbose_name=_("resultat del curs"),
    )  # fmt: skip
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("titulació")
        verbose_name_plural = _("titulacions")
        ordering = ["person_id", "pk"]
        indexes = [models.Index(fields=["person"], name="divercert_person_idx")]
        constraints = [
            models.CheckConstraint(
                condition=Q(level__isnull=False) | Q(speciality__isnull=False),
                name="divercert_level_or_speciality",
            ),
            models.CheckConstraint(
                condition=Q(source__in=["club_course", "declared", "imported", "federation"]),
                name="divercert_source_valid",
            ),
            models.CheckConstraint(
                condition=Q(verified_by__isnull=True, verified_at__isnull=True)
                | Q(verified_by__isnull=False, verified_at__isnull=False),
                name="divercert_verified_by_and_at_together",
            ),
        ]

    def __str__(self):
        return str(self.level or self.speciality)

    @property
    def is_verified(self) -> bool:
        return self.verified_by_id is not None


class EnvironmentalResult(models.Model):
    """Resultats d'una sortida de medi ambient (T-M02-20; M02-6; P-M02-G; S-M02-14): residus,
    espècies observades i observacions. Un per sortida. No es publica enlloc des del 02
    (RN-M02-23). Les fotos encara no existeixen (vegeu `environment.py`)."""

    activity = models.OneToOneField(
        Activity,
        on_delete=models.PROTECT,
        related_name="environmental_result",
        verbose_name=_("sortida"),
    )
    # Els quilos s'escriuen amb decimals i es desen en grams (enter).
    waste_grams = models.PositiveIntegerField(_("residus recollits (grams)"), null=True, blank=True)
    # Una espècie per línia.
    species = models.TextField(_("espècies observades"), blank=True)
    # Sense dades de salut (RN-M02-17).
    observations = models.TextField(_("observacions"), blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("registrat per"),
    )
    recorded_at = models.DateTimeField(_("registrat el"))

    class Meta:
        verbose_name = _("resultats ambientals")
        verbose_name_plural = _("resultats ambientals")

    def __str__(self):
        return str(self.activity)


class Enrolment(models.Model):
    """Inscripció d'una persona a una activitat (M02-6; RN-M02-03, RN-M02-04 i RN-M02-07). El model
    arriba amb la T-M02-10 (confirmar-la quan es paga el càrrec); inscriure's és de la T-M02-11.

    Ocupen plaça les inscripcions pendents de pagament, confirmades i amb una plaça oferta
    (`OCCUPYING`). Una persona només pot tenir una inscripció viva per activitat."""

    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", _("Pendent de pagament")
        CONFIRMED = "confirmed", _("Confirmada")
        WAITLISTED = "waitlisted", _("En llista d'espera")
        OFFERED = "offered", _("Plaça oferta")
        CANCELLED = "cancelled", _("Cancel·lada")
        EXPIRED = "expired", _("Caducada")

    class Channel(models.TextChoices):
        ACCOUNT = "account", _("Compte personal")
        GUEST = "guest", _("Convidat")
        DESK = "desk", _("Presencial")

    class PriceKind(models.TextChoices):
        MEMBER = "member", _("Soci")
        NON_MEMBER = "non_member", _("No soci")

    OCCUPYING = (Status.PENDING_PAYMENT, Status.CONFIRMED, Status.OFFERED)
    LIVE = (*OCCUPYING, Status.WAITLISTED)
    ENDED = (Status.CANCELLED, Status.EXPIRED)

    activity = models.ForeignKey(
        Activity, on_delete=models.PROTECT, related_name="enrolments", verbose_name=_("activitat")
    )
    person = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,
        related_name="activity_enrolments",
        verbose_name=_("persona"),
    )
    status = models.CharField(_("estat"), max_length=20, choices=Status.choices)
    channel = models.CharField(_("canal"), max_length=10, choices=Channel.choices)
    # Fixats en inscriure's: no canvien encara que canviï el catàleg o l'estat de soci (RN-M02-04).
    price_kind = models.CharField(_("preu aplicat"), max_length=10, choices=PriceKind.choices)
    price_cents = models.PositiveIntegerField(_("preu (cèntims)"))
    # Buit si és gratuïta o si encara és a la llista d'espera.
    charge = models.ForeignKey(
        "core.Charge",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("càrrec"),
    )
    waitlist_position = models.PositiveIntegerField(
        _("posició a la llista d'espera"), null=True, blank=True
    )
    payment_due_at = models.DateTimeField(_("termini de pagament"), null=True, blank=True)
    offer_expires_at = models.DateTimeField(_("termini de l'oferta"), null=True, blank=True)
    # Què no complia en inscriure's. Sense dades de salut ni de la llicència (RN-M01-48).
    requirements_warning = models.TextField(_("requisits per revisar"), blank=True)
    cancelled_reason = models.TextField(_("motiu de la cancel·lació"), blank=True)
    # RN-M02-37: cancel·lada amb un pagament en curs; el càrrec s'anul·la quan l'intent acaba.
    void_pending_since = models.DateTimeField(
        _("càrrec per anul·lar des de"), null=True, blank=True
    )
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("cancel·lada per"),
    )
    # Buit = el mateix participant o el seu enllaç.
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("feta per"),
    )
    created_at = models.DateTimeField(_("feta el"))
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("inscripció")
        verbose_name_plural = _("inscripcions")
        ordering = ["created_at", "id"]
        indexes = [models.Index(fields=["activity", "status"], name="enrolment_activity_status")]
        constraints = [
            models.UniqueConstraint(
                fields=["activity", "person"],
                condition=~Q(status__in=["cancelled", "expired"]),
                name="enrolment_one_live_per_person",
            ),
            models.CheckConstraint(
                condition=Q(status="waitlisted") | Q(waitlist_position__isnull=True),
                name="enrolment_position_only_waitlisted",
            ),
            models.CheckConstraint(
                condition=~Q(status="cancelled") | ~Q(cancelled_reason=""),
                name="enrolment_cancelled_needs_reason",
            ),
            models.CheckConstraint(
                condition=Q(
                    status__in=[
                        "pending_payment",
                        "confirmed",
                        "waitlisted",
                        "offered",
                        "cancelled",
                        "expired",
                    ]
                ),
                name="enrolment_status_valid",
            ),
        ]

    def __str__(self):
        return f"{self.activity} · {self.get_status_display()}"

    @property
    def occupies_place(self) -> bool:
        return self.status in self.OCCUPYING


class RefundProposal(models.Model):
    """Proposta de devolució d'una inscripció cancel·lada després de pagar-la (M02-6; RN-M02-12 i
    RN-M02-13; CA-M02-14 i CA-M02-15; S-M02-23). Cap devolució automàtica: el tresorer (AC18) la
    fa amb el 05b (`payments.refund`, idempotent per `refund_key`) o la rebutja amb motiu."""

    class Status(models.TextChoices):
        PROPOSED = "proposed", _("Proposada")
        DONE = "done", _("Feta")
        REJECTED = "rejected", _("Rebutjada")

    enrolment = models.OneToOneField(
        Enrolment, on_delete=models.PROTECT, related_name="refund_proposal",
        verbose_name=_("inscripció"),
    )  # fmt: skip
    charge = models.ForeignKey(
        "core.Charge", on_delete=models.PROTECT, related_name="+", verbose_name=_("càrrec")
    )
    amount_cents = models.PositiveIntegerField(_("import (cèntims)"))
    reason = models.TextField(_("motiu"))
    # Buit = el sistema (cancel·lació del participant o de l'activitat).
    proposed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="+", verbose_name=_("proposada per"),
    )  # fmt: skip
    status = models.CharField(
        _("estat"), max_length=8, choices=Status.choices, default=Status.PROPOSED
    )
    refund = models.ForeignKey(
        "payments.RefundRequest", on_delete=models.PROTECT, null=True, blank=True,
        related_name="+", verbose_name=_("devolució"),
    )  # fmt: skip
    refund_key = models.UUIDField(_("clau de la devolució"), default=uuid.uuid4, unique=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="+", verbose_name=_("decidida per"),
    )  # fmt: skip
    decision_reason = models.TextField(_("motiu de la decisió"), blank=True)
    decided_at = models.DateTimeField(_("decidida el"), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("proposta de devolució d'una inscripció")
        verbose_name_plural = _("propostes de devolució d'inscripcions")
        constraints = [
            models.CheckConstraint(
                condition=Q(amount_cents__gt=0), name="activities_refund_amount_positive"
            ),
            models.CheckConstraint(
                condition=Q(status__in=["proposed", "done", "rejected"]),
                name="activities_refund_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(status="proposed") | Q(decided_by__isnull=False),
                name="activities_refund_decided_has_author",
            ),
        ]

    def __str__(self):
        return f"{self.enrolment} · {self.get_status_display()}"


class Attendance(models.Model):
    """Assistència d'un inscrit a una sessió d'un curs o, sense sessió, al dia d'una sortida
    (T-M02-16; M02-6; P-M02-E). Es pot corregir: cada canvi queda al registre d'activitat amb el
    valor anterior. Només canvia amb `apps.activities.attendance`."""

    enrolment = models.ForeignKey(
        Enrolment, on_delete=models.PROTECT, related_name="attendance", verbose_name=_("inscripció")
    )
    # Buit = el dia de la sortida.
    session = models.ForeignKey(
        Session,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="attendance",
        verbose_name=_("sessió"),
    )
    present = models.BooleanField(_("hi és"))
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("registrat per"),
    )
    recorded_at = models.DateTimeField(_("registrat el"))

    class Meta:
        verbose_name = _("assistència")
        verbose_name_plural = _("assistències")
        constraints = [
            models.UniqueConstraint(
                fields=["enrolment", "session"],
                condition=Q(session__isnull=False),
                name="attendance_one_per_session",
            ),
            models.UniqueConstraint(
                fields=["enrolment"],
                condition=Q(session__isnull=True),
                name="attendance_one_per_outing",
            ),
        ]

    def __str__(self):
        return f"{self.enrolment_id} · {self.present}"


class Incident(AppendOnlyModel):
    """Incidència operativa d'una activitat (T-M02-16; M02-6; P-M02-E pas 3): retard, embarcació,
    material, meteorologia o una altra. Només s'hi afegeixen. **Mai dades de salut** (RN-M02-17):
    un accident segueix el protocol del club fora de la plataforma."""

    class Kind(models.TextChoices):
        DELAY = "delay", _("Retard")
        BOAT = "boat", _("Embarcació")
        EQUIPMENT = "equipment", _("Material")
        WEATHER = "weather", _("Meteorologia")
        OTHER = "other", _("Una altra")

    activity = models.ForeignKey(
        Activity, on_delete=models.PROTECT, related_name="incidents", verbose_name=_("activitat")
    )
    session = models.ForeignKey(
        Session,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="incidents",
        verbose_name=_("sessió"),
    )
    kind = models.CharField(_("classe"), max_length=10, choices=Kind.choices)
    # Sense dades de salut (RN-M02-17).
    description = models.TextField(_("descripció"), max_length=1000)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("registrada per"),
    )
    recorded_at = models.DateTimeField(_("registrada el"))

    class Meta:
        verbose_name = _("incidència")
        verbose_name_plural = _("incidències")
        ordering = ["-recorded_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(kind__in=["delay", "boat", "equipment", "weather", "other"]),
                name="incident_kind_valid",
            ),
        ]

    def __str__(self):
        return f"{self.get_kind_display()} · {self.activity}"


class PracticeAssessment(models.Model):
    """Avaluació d'un alumne en una sessió pràctica (T-M02-17; M02-6; P-M02-F pas 1). Es pot
    corregir; cada canvi queda al registre. Sense dades de salut (RN-M02-17)."""

    class Result(models.TextChoices):
        ACHIEVED = "achieved", _("Assolit")
        NOT_ACHIEVED = "not_achieved", _("No assolit")
        NEEDS_REINFORCEMENT = "needs_reinforcement", _("Necessita reforç")

    session = models.ForeignKey(
        Session, on_delete=models.PROTECT, related_name="assessments", verbose_name=_("sessió")
    )
    enrolment = models.ForeignKey(
        Enrolment, on_delete=models.PROTECT, related_name="assessments",
        verbose_name=_("inscripció"),
    )  # fmt: skip
    result = models.CharField(_("resultat"), max_length=20, choices=Result.choices)
    # Observació curta. Sense dades de salut (RN-M02-17).
    notes = models.TextField(_("observació"), max_length=500, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+",
        verbose_name=_("registrada per"),
    )  # fmt: skip
    recorded_at = models.DateTimeField(_("registrada el"))

    class Meta:
        verbose_name = _("avaluació d'una pràctica")
        verbose_name_plural = _("avaluacions de pràctiques")
        constraints = [
            models.UniqueConstraint(
                fields=["session", "enrolment"], name="assessment_one_per_session_and_student"
            ),
            models.CheckConstraint(
                condition=Q(result__in=["achieved", "not_achieved", "needs_reinforcement"]),
                name="assessment_result_valid",
            ),
        ]

    def __str__(self):
        return f"{self.enrolment_id} · {self.get_result_display()}"


class CourseOutcome(models.Model):
    """Resultat final d'un alumne en un curs i, si és apte, el certificat del club (T-M02-19;
    M02-6; RN-M02-16). El certificat no es desa com a fitxer: es genera a demanda."""

    class Result(models.TextChoices):
        PASS = "pass", _("Apte")
        FAIL = "fail", _("No apte")

    enrolment = models.OneToOneField(
        Enrolment, on_delete=models.PROTECT, related_name="outcome", verbose_name=_("inscripció")
    )
    result = models.CharField(_("resultat"), max_length=10, choices=Result.choices)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+",
        verbose_name=_("instructor que el posa"),
    )  # fmt: skip
    decided_at = models.DateTimeField(_("posat el"))
    # Obligatori si és «no apte». Sense dades de salut (RN-M02-17).
    reason = models.TextField(_("motiu"), max_length=500, blank=True)
    # `C-AAAA-NNNN` (VC-26, format al codi). Buit fins que s'emet.
    certificate_number = models.CharField(_("número del certificat"), max_length=20, blank=True)
    certificate_issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="+", verbose_name=_("certificat emès per"),
    )  # fmt: skip
    certificate_issued_at = models.DateTimeField(_("certificat emès el"), null=True, blank=True)

    class Meta:
        verbose_name = _("resultat del curs")
        verbose_name_plural = _("resultats dels cursos")
        constraints = [
            models.UniqueConstraint(
                fields=["certificate_number"],
                condition=~Q(certificate_number=""),
                name="outcome_certificate_number_unique",
            ),
            models.CheckConstraint(
                condition=Q(result__in=["pass", "fail"]), name="outcome_result_valid"
            ),
            models.CheckConstraint(
                condition=~Q(result="fail") | ~Q(reason=""), name="outcome_fail_needs_reason"
            ),
            models.CheckConstraint(
                condition=Q(certificate_number="") | Q(result="pass"),
                name="outcome_certificate_only_if_pass",
            ),
        ]

    def __str__(self):
        return f"{self.enrolment_id} · {self.get_result_display()}"
