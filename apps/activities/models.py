"""Models del mòdul 02, Activitats (cursos i sortides).

- **Catàleg** (T-M02-02; M02-6; RN-M02-01 i RN-M02-05; VC-20): fitxes de cursos i d'especialitats,
  preus amb versions, tipus de sortida, subtipus i projectes.
- **Activitat, sessió i bloc de programa** (T-M02-03; M02-6; RN-M02-02 i RN-M02-20).
- **Nivells, requisits i titulacions** (T-M02-23, T-M02-29 i T-M02-32; addenda de la 058):
  `CertificationLevel`, els camps de requisits de l'activitat i `DiverCertification`.

Regles comunes:
- Imports en cèntims (enters, ≥ 0: una activitat pot ser gratuïta, L-M02-06).
- Cap dada de salut, de targeta ni d'IBAN (CA-M02-25).
- Les fitxes, els tipus, els subtipus i els projectes no s'esborren si tenen activitats (PROTECT):
  es desactiven.
- Res no es desa directament: el catàleg canvia amb `apps.activities.catalogue`, les activitats amb
  `apps.activities.services`, l'estat amb `apps.activities.states` i les sessions i el programa amb
  `apps.activities.sessions`.

Encara no existeixen, i cap codi no els simula: `Activity.cost_centre` (el centre de cost és de la
04), `Session.reinforcement_for` (la inscripció és de la T-M02-11),
`DiverCertification.course_outcome` (el resultat del curs és de la T-M02-19) i la resta
d'entitats (inscripcions, assistència, avaluacions i resultats ambientals).
"""

from django.conf import settings
from django.db import models
from django.db.models import F, Q
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
    # Mode de requisits que copien les activitats noves (RN-M02-29). Buit: val l'ajust general.
    default_requirements_mode = models.CharField(
        _("mode de requisits per defecte"),
        max_length=5,
        choices=RequirementsMode.choices,
        blank=True,
        default="",
    )
    # Edat mínima que copien les activitats noves (RN-M02-33). Buit: sense edat mínima.
    min_age = models.PositiveSmallIntegerField(_("edat mínima"), null=True, blank=True)
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
    # Mode de requisits que copien les activitats noves (RN-M02-29). Buit: val l'ajust general.
    default_requirements_mode = models.CharField(
        _("mode de requisits per defecte"),
        max_length=5,
        choices=RequirementsMode.choices,
        blank=True,
        default="",
    )
    active = models.BooleanField(_("actiu"), default=True)

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


class CertificationLevel(models.Model):
    """Nivell de titulació de busseig, amb un ordre: un `rank` més alt és un nivell més alt
    (addenda de la 058; RN-M02-27). La llista la manté el responsable de cursos i sortides; no
    porta dades inicials [A verificar: FECDAS, S-M02-11]."""

    name = models.CharField(_("nom"), max_length=60, unique=True)
    rank = models.PositiveSmallIntegerField(_("ordre"), unique=True)
    agency = models.CharField(_("agència o federació"), max_length=60, blank=True)
    active = models.BooleanField(_("actiu"), default=True)

    class Meta:
        verbose_name = _("nivell de titulació")
        verbose_name_plural = _("nivells de titulació")
        ordering = ["rank"]

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

    class SpecialitiesRule(models.TextChoices):
        ALL = "all", _("Totes")
        ANY = "any", _("Alguna")

    RequirementsMode = RequirementsMode  # el mateix de les fitxes i els tipus (RN-M02-29)

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
    # Requisits de l'addenda de la 058 (RN-M02-27, 28 i 33). `min_level` fa la funció de
    # `required_level`, que queda com a text informatiu.
    min_level = models.ForeignKey(
        CertificationLevel,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="activities",
        verbose_name=_("nivell mínim"),
    )
    required_specialities = models.ManyToManyField(
        TrainingCatalogueEntry,
        blank=True,
        related_name="required_by",
        verbose_name=_("especialitats exigides"),
    )
    specialities_rule = models.CharField(
        _("quantes especialitats calen"),
        max_length=3,
        choices=SpecialitiesRule.choices,
        default=SpecialitiesRule.ALL,
    )
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
                condition=Q(specialities_rule__in=["all", "any"]),
                name="activity_specialities_rule_valid",
            ),
            models.CheckConstraint(
                condition=Q(min_age__isnull=True) | Q(min_age__gte=1, min_age__lte=99),
                name="activity_min_age_valid",
            ),
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
        null=True,
        blank=True,
        related_name="certifications",
        verbose_name=_("especialitat"),
    )
    agency = models.CharField(_("agència o federació"), max_length=60, blank=True)
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
                condition=Q(source__in=["club_course", "declared", "imported"]),
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
    (RN-M02-23). Les fotos encara no existeixen."""

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
