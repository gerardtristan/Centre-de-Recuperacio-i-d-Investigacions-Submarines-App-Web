"""Material (mòdul 03; M03-6). Imports en cèntims. Les FK cap al 02 són només de lectura: el 03 no
hi escriu mai. Cap dada personal."""

from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateRangeField, RangeOperators
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


class TypicalEquipmentTemplate(models.Model):
    """Material típic d'una fitxa del catàleg o d'un tipus de sortida del 02 (M03-6; RN-M03-17):
    el que fa servir cada participant. La còpia a l'activitat és de la T-M03-06."""

    catalogue_entry = models.ForeignKey(
        "activities.TrainingCatalogueEntry",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("fitxa del catàleg"),
    )
    outing_type = models.ForeignKey(
        "activities.OutingType",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("tipus de sortida"),
    )
    equipment_type = models.ForeignKey(
        EquipmentType, on_delete=models.PROTECT, related_name="+", verbose_name=_("tipus")
    )
    quantity_per_participant = models.PositiveSmallIntegerField(_("quantitat per participant"))

    class Meta:
        verbose_name = _("material típic")
        verbose_name_plural = _("material típic")
        constraints = [
            models.CheckConstraint(
                condition=Q(catalogue_entry__isnull=False, outing_type__isnull=True)
                | Q(catalogue_entry__isnull=True, outing_type__isnull=False),
                name="typical_equipment_one_owner",
            ),
            models.CheckConstraint(
                condition=Q(quantity_per_participant__gt=0), name="typical_equipment_quantity"
            ),
        ]

    def __str__(self):
        return f"{self.equipment_type} × {self.quantity_per_participant}"


class UsageRate(models.Model):
    """Cost d'ús d'un tipus de material del club per dia (RN-M03-08; VC-28): sense cap fila, 0.
    El canvia el tresorer a la pantalla d'ajustos (T-M03-22), amb data d'entrada en vigor."""

    equipment_type = models.ForeignKey(
        EquipmentType, on_delete=models.PROTECT, related_name="+", verbose_name=_("tipus")
    )
    cost_per_day_cents = models.PositiveIntegerField(_("cost per dia (cèntims)"))
    valid_from = models.DateField(_("vigent des de"))

    class Meta:
        verbose_name = _("cost d'ús")
        verbose_name_plural = _("costos d'ús")
        constraints = [
            models.UniqueConstraint(
                fields=["equipment_type", "valid_from"], name="usage_rate_unique_start"
            )
        ]

    def __str__(self):
        return f"{self.equipment_type}: {self.cost_per_day_cents} c/dia"


class ActivityTypicalEquipment(models.Model):
    """Material típic d'una activitat (M03-6; RN-M03-17): es copia de la plantilla en crear-la i
    de l'original en duplicar-la. El 03 no escriu mai a l'activitat."""

    activity = models.ForeignKey(
        "activities.Activity",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("activitat"),
    )
    equipment_type = models.ForeignKey(
        EquipmentType, on_delete=models.PROTECT, related_name="+", verbose_name=_("tipus")
    )
    quantity_per_participant = models.PositiveSmallIntegerField(_("quantitat per participant"))

    class Meta:
        verbose_name = _("material típic d'una activitat")
        verbose_name_plural = _("material típic de les activitats")
        constraints = [
            models.UniqueConstraint(
                fields=["activity", "equipment_type"], name="activity_typical_unique"
            ),
            models.CheckConstraint(
                condition=Q(quantity_per_participant__gt=0), name="activity_typical_quantity"
            ),
        ]

    def __str__(self):
        return f"{self.equipment_type} × {self.quantity_per_participant}"


class EquipmentItem(models.Model):
    """Peça de l'inventari del club (M03-6, T-M03-03). Una peça amb assignacions no s'esborra: es
    dona de baixa (`retired`, amb motiu). «Assignada», «en ús» i «retornada» surten de les
    assignacions (RN-M03-04)."""

    class Status(models.TextChoices):
        AVAILABLE = "available", _("Disponible")
        IN_REVIEW = "in_review", _("En revisió")
        RETIRED = "retired", _("Donada de baixa")

    code = models.CharField(_("codi"), max_length=20, unique=True)
    type = models.ForeignKey(
        EquipmentType, on_delete=models.PROTECT, related_name="items", verbose_name=_("tipus")
    )
    size = models.CharField(_("talla"), max_length=10, blank=True)
    litres = models.DecimalField(_("litres"), max_digits=4, decimal_places=1, null=True, blank=True)
    status = models.CharField(
        _("estat"), max_length=9, choices=Status.choices, default=Status.AVAILABLE
    )
    purchased_on = models.DateField(_("data de compra"), null=True, blank=True)
    purchase_cost_cents = models.PositiveIntegerField(
        _("cost de compra (cèntims)"), null=True, blank=True
    )
    next_review_on = models.DateField(_("propera revisió"), null=True, blank=True)
    retired_reason = models.TextField(_("motiu de la baixa"), blank=True)
    notes = models.TextField(_("notes"), blank=True)
    created_at = models.DateTimeField(_("creada"), auto_now_add=True)

    class Meta:
        verbose_name = _("peça de material")
        verbose_name_plural = _("peces de material")
        ordering = ["code"]
        indexes = [
            models.Index(
                fields=["type", "size", "litres", "status"], name="equipment_item_stock_idx"
            )
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=["available", "in_review", "retired"]),
                name="equipment_item_status",
            ),
            models.CheckConstraint(
                condition=Q(litres__isnull=True) | Q(litres__gt=0), name="equipment_item_litres"
            ),
            models.CheckConstraint(
                condition=~Q(status="retired") | ~Q(retired_reason=""),
                name="equipment_item_retired_reason",
            ),
            models.CheckConstraint(condition=~Q(code=""), name="equipment_item_code"),
        ]

    def __str__(self):
        return self.code


class EquipmentReview(models.Model):
    """Revisió d'una peça (M03-6, T-M03-14). Un cop tancada (`done_on`), no es modifica. La data
    la posa el responsable segons la normativa o el fabricant (RN-M03-15)."""

    class Kind(models.TextChoices):
        HYDROSTATIC_TEST = "hydrostatic_test", _("Prova hidràulica")
        VISUAL_INSPECTION = "visual_inspection", _("Inspecció visual")
        REGULATOR_SERVICE = "regulator_service", _("Revisió del regulador")
        OTHER = "other", _("Una altra")

    class Result(models.TextChoices):
        OK = "ok", _("Correcta")
        FAILED = "failed", _("Fallida")

    item = models.ForeignKey(
        EquipmentItem, on_delete=models.PROTECT, related_name="reviews", verbose_name=_("peça")
    )
    kind = models.CharField(_("tipus"), max_length=20, choices=Kind.choices)
    due_on = models.DateField(_("prevista el"))
    sent_on = models.DateField(_("enviada el"), null=True, blank=True)
    done_on = models.DateField(_("feta el"), null=True, blank=True)
    provider = models.CharField(_("qui la fa"), max_length=120, blank=True)
    # NULL (i no text buit) mentre no està feta: la restricció distingeix «sense resultat».
    result = models.CharField(  # noqa: DJ001
        _("resultat"), max_length=6, choices=Result.choices, null=True, blank=True
    )
    cost_cents = models.PositiveIntegerField(_("cost (cèntims)"), null=True, blank=True)
    next_review_on = models.DateField(_("propera revisió"), null=True, blank=True)
    notes = models.TextField(_("notes"), blank=True)
    recorded_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("registrada per"),
    )

    class Meta:
        verbose_name = _("revisió de material")
        verbose_name_plural = _("revisions de material")
        ordering = ["due_on", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=Q(
                    kind__in=["hydrostatic_test", "visual_inspection", "regulator_service", "other"]
                ),
                name="equipment_review_kind",
            ),
            # Feta, sempre amb resultat; amb resultat, sempre feta. `isnull=False` explícit: amb
            # NULL, `IN` donaria «desconegut» i PostgreSQL deixaria passar la restricció.
            models.CheckConstraint(
                condition=Q(done_on__isnull=True, result__isnull=True)
                | Q(done_on__isnull=False, result__isnull=False, result__in=["ok", "failed"]),
                name="equipment_review_done_has_result",
            ),
            models.UniqueConstraint(
                fields=["item"], condition=Q(done_on__isnull=True), name="equipment_review_one_open"
            ),
        ]

    def __str__(self):
        return f"{self.item} {self.get_kind_display()} ({self.due_on})"


class EquipmentNeed(models.Model):
    """Què porta i què necessita un participant (M03-6; P-M03-C; T-M03-07). Es desa amb la
    inscripció, també a la llista d'espera. El 03 no escriu mai a la inscripció."""

    enrolment = models.ForeignKey(
        "activities.Enrolment",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("inscripció"),
    )
    equipment_type = models.ForeignKey(
        EquipmentType, on_delete=models.PROTECT, related_name="+", verbose_name=_("tipus")
    )
    brings_own = models.BooleanField(_("porta el seu"))
    size = models.CharField(_("talla"), max_length=10, blank=True)
    litres = models.DecimalField(_("litres"), max_digits=4, decimal_places=1, null=True, blank=True)

    class Meta:
        verbose_name = _("necessitat de material")
        verbose_name_plural = _("necessitats de material")
        constraints = [
            models.UniqueConstraint(
                fields=["enrolment", "equipment_type"], name="equipment_need_unique"
            ),
            models.CheckConstraint(
                condition=Q(litres__isnull=True) | Q(litres__gt=0), name="equipment_need_litres"
            ),
        ]

    def __str__(self):
        return f"{self.equipment_type} · {'propi' if self.brings_own else 'necessita'}"


class EquipmentAssignment(models.Model):
    """Material d'un participant en una activitat (M03-6; P-M03-D; T-M03-08): propi, del club
    (una peça) o llogat a un centre (amb la tarifa copiada, RN-M03-06). La restricció d'exclusió
    garanteix que una peça del club no és en dues assignacions vives amb dies que es toquin, també
    si dues persones assignen alhora (RN-M03-02)."""

    class Origin(models.TextChoices):
        OWN = "own", _("Propi")
        CLUB = "club", _("Del club")
        RENTED = "rented", _("Llogat")

    class Status(models.TextChoices):
        PLANNED = "planned", _("Prevista")
        DELIVERED = "delivered", _("Lliurada")
        RETURNED = "returned", _("Retornada")
        NOT_USED = "not_used", _("No s'ha fet servir")
        CANCELLED = "cancelled", _("Cancel·lada")

    LIVE = (Status.PLANNED, Status.DELIVERED)

    activity = models.ForeignKey(
        "activities.Activity", on_delete=models.PROTECT, related_name="+",
        verbose_name=_("activitat"),
    )  # fmt: skip
    enrolment = models.ForeignKey(
        "activities.Enrolment", on_delete=models.PROTECT, related_name="+",
        verbose_name=_("inscripció"),
    )  # fmt: skip
    # Només per a una classe de reforç (RN-M03-19).
    session = models.ForeignKey(
        "activities.Session", on_delete=models.PROTECT, null=True, blank=True, related_name="+",
        verbose_name=_("sessió"),
    )  # fmt: skip
    equipment_type = models.ForeignKey(
        EquipmentType, on_delete=models.PROTECT, related_name="+", verbose_name=_("tipus")
    )
    origin = models.CharField(_("origen"), max_length=6, choices=Origin.choices)
    item = models.ForeignKey(
        EquipmentItem, on_delete=models.PROTECT, null=True, blank=True,
        related_name="assignments", verbose_name=_("peça"),
    )  # fmt: skip
    centre = models.ForeignKey(
        DiveCentre, on_delete=models.PROTECT, null=True, blank=True, related_name="+",
        verbose_name=_("centre"),
    )  # fmt: skip
    rate = models.ForeignKey(
        CentreRate, on_delete=models.PROTECT, null=True, blank=True, related_name="+",
        verbose_name=_("tarifa"),
    )  # fmt: skip
    period = DateRangeField(_("dies"))
    cost_cents = models.PositiveIntegerField(_("cost per al club (cèntims)"))
    participant_price_cents = models.PositiveIntegerField(_("preu per al participant (cèntims)"))
    status = models.CharField(
        _("estat"), max_length=9, choices=Status.choices, default=Status.PLANNED
    )
    delivered_at = models.DateTimeField(_("lliurada el"), null=True, blank=True)
    returned_at = models.DateTimeField(_("retornada el"), null=True, blank=True)
    note = models.TextField(_("nota"), blank=True)
    created_by = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, related_name="+", verbose_name=_("feta per")
    )
    created_at = models.DateTimeField(_("feta el"), auto_now_add=True)

    class Meta:
        verbose_name = _("assignació de material")
        verbose_name_plural = _("assignacions de material")
        ordering = ["activity", "enrolment", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=Q(origin__in=["own", "club", "rented"]), name="assignment_origin"
            ),
            models.CheckConstraint(
                condition=Q(
                    status__in=["planned", "delivered", "returned", "not_used", "cancelled"]
                ),
                name="assignment_status",
            ),
            models.CheckConstraint(
                condition=Q(origin="club", item__isnull=False)
                | (~Q(origin="club") & Q(item__isnull=True)),
                name="assignment_item_iff_club",
            ),
            models.CheckConstraint(
                condition=Q(origin="rented", centre__isnull=False, rate__isnull=False)
                | (~Q(origin="rented") & Q(centre__isnull=True, rate__isnull=True)),
                name="assignment_rate_iff_rented",
            ),
            # RN-M03-02: la garantia és a la base de dades (extensió `btree_gist`).
            ExclusionConstraint(
                name="assignment_item_no_overlap",
                expressions=[("item", RangeOperators.EQUAL), ("period", RangeOperators.OVERLAPS)],
                condition=Q(item__isnull=False, status__in=["planned", "delivered"]),
            ),
        ]

    def __str__(self):
        return f"{self.equipment_type} · {self.get_origin_display()} · {self.get_status_display()}"


class RentalList(models.Model):
    """Una llista de lloguer generada per a un centre (M03-6; RN-M03-18; T-M03-10). El contingut
    es genera a demanda i no es desa: només l'empremta, qui i quan, i si s'ha enviat."""

    activity = models.ForeignKey(
        "activities.Activity", on_delete=models.PROTECT, related_name="+",
        verbose_name=_("activitat"),
    )  # fmt: skip
    centre = models.ForeignKey(
        DiveCentre, on_delete=models.PROTECT, related_name="+", verbose_name=_("centre")
    )
    generated_by = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, related_name="+",
        verbose_name=_("generada per"),
    )  # fmt: skip
    generated_at = models.DateTimeField(_("generada el"))
    fingerprint = models.CharField(_("empremta"), max_length=64)
    sent_at = models.DateTimeField(_("enviada el"), null=True, blank=True)
    sent_by = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, null=True, blank=True, related_name="+",
        verbose_name=_("enviada per"),
    )  # fmt: skip

    class Meta:
        verbose_name = _("llista de lloguer")
        verbose_name_plural = _("llistes de lloguer")
        ordering = ["-generated_at", "-pk"]
        constraints = [
            models.CheckConstraint(
                condition=Q(sent_at__isnull=True, sent_by__isnull=True)
                | Q(sent_at__isnull=False, sent_by__isnull=False),
                name="rental_list_sent_by_and_at",
            ),
        ]

    def __str__(self):
        return f"{self.centre} · {self.activity_id}"
