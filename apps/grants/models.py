"""Ajuts: convocatòria, documents requerits i sol·licitud (M09-ajuts-6, T-M09A-02). Cap dada
personal de socis ni participants (RN-M09A-15): només el responsable i qui fa cada acció.

Els fitxers (bases, còpia presentada, resolució, documents) són només un lligam a un fitxer
privat de la 00: pujar-los, xifrar-los i qui els obre és de la T-M09-25 (051). La denegació, els
requeriments, les despeses lligades, els paquets i els avisos arriben amb les seves tasques."""

from django.db import models
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _

from apps.core.models import AppendOnlyModel


def _file(label):
    return models.ForeignKey(
        "core.PrivateFile",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=label,
    )


class GrantCall(models.Model):
    class Eligibility(models.TextChoices):
        PENDING = "pending", _("Pendent de revisar")
        ELIGIBLE = "eligible", _("Elegible")
        NOT_ELIGIBLE = "not_eligible", _("No elegible")

    class MaskedProofs(models.TextChoices):
        YES = "yes", _("Sí")
        NO = "no", _("No")
        UNKNOWN = "unknown", _("No se sap")

    body = models.CharField(_("organisme"), max_length=140)
    name = models.CharField(_("nom"), max_length=200)
    edition_label = models.CharField(_("edició"), max_length=20, blank=True)
    # Sense tancament: oberta tot l'any, sense avisos de tancament (L-M09A-01).
    opens_on = models.DateField(_("obertura"), null=True, blank=True)
    closes_on = models.DateField(_("tancament"), null=True, blank=True)
    max_amount_cents = models.PositiveBigIntegerField(_("import màxim"), null=True, blank=True)
    # La plataforma no el visita mai.
    rules_url = models.URLField(_("enllaç a les bases"), blank=True)
    rules_file = _file(_("còpia de les bases"))
    eligibility_requirements = models.TextField(_("requisits d'elegibilitat"), blank=True)
    # Només el canvia una persona (RN-M09A-03).
    eligibility_status = models.CharField(
        _("elegibilitat"), max_length=12, choices=Eligibility.choices, default=Eligibility.PENDING
    )
    eligibility_reviewed_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("revisada per"),
    )
    eligibility_reviewed_at = models.DateTimeField(_("revisada"), null=True, blank=True)
    eligibility_notes = models.TextField(_("notes de l'elegibilitat"), blank=True)
    max_resolution_days = models.PositiveSmallIntegerField(
        _("termini màxim de resolució (dies)"), null=True, blank=True
    )
    eligible_expenses_from = models.DateField(_("despeses des de"), null=True, blank=True)
    eligible_expenses_to = models.DateField(_("despeses fins a"), null=True, blank=True)
    justification_due_on = models.DateField(_("data de justificació"), null=True, blank=True)
    justification_format = models.TextField(_("format de la justificació"), blank=True)
    # 051: si l'organisme accepta comprovants amb l'IBAN emmascarat [A verificar: tresorer].
    accepts_masked_proofs = models.CharField(
        _("accepta còpies emmascarades"),
        max_length=7,
        choices=MaskedProofs.choices,
        default=MaskedProofs.UNKNOWN,
    )
    previous_edition = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("edició anterior"),
    )
    created_by = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, related_name="+", verbose_name=_("creada per")
    )
    created_at = models.DateTimeField(_("creada"), auto_now_add=True)

    class Meta:
        verbose_name = _("convocatòria d'ajut")
        verbose_name_plural = _("convocatòries d'ajut")
        constraints = [
            models.CheckConstraint(
                condition=Q(closes_on__isnull=True)
                | Q(opens_on__isnull=True)
                | Q(closes_on__gte=F("opens_on")),
                name="grant_call_dates_in_order",
            ),
            models.CheckConstraint(
                condition=Q(eligible_expenses_to__isnull=True)
                | Q(eligible_expenses_from__isnull=True)
                | Q(eligible_expenses_to__gte=F("eligible_expenses_from")),
                name="grant_call_expense_period_in_order",
            ),
            models.CheckConstraint(
                condition=Q(eligibility_status__in=["pending", "eligible", "not_eligible"]),
                name="grant_call_eligibility_valid",
            ),
            # RN-M09A-03: una revisió sempre diu qui, quan i per què.
            models.CheckConstraint(
                condition=Q(eligibility_status="pending")
                | (
                    Q(eligibility_reviewed_by__isnull=False)
                    & Q(eligibility_reviewed_at__isnull=False)
                    & ~Q(eligibility_notes="")
                ),
                name="grant_call_eligibility_reviewed",
            ),
            models.CheckConstraint(
                condition=Q(accepts_masked_proofs__in=["yes", "no", "unknown"]),
                name="grant_call_masked_proofs_valid",
            ),
        ]

    def __str__(self):
        return f"{self.body}: {self.name} {self.edition_label}".strip()


class GrantCallDocument(models.Model):
    """Document que demana la convocatòria (un per línia, P-M09A-A)."""

    call = models.ForeignKey(
        GrantCall,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name=_("convocatòria"),
    )
    name = models.CharField(_("document"), max_length=200)
    order = models.PositiveSmallIntegerField(_("ordre"), default=0)

    class Meta:
        verbose_name = _("document requerit")
        verbose_name_plural = _("documents requerits")
        ordering = ["order", "pk"]
        constraints = [
            models.UniqueConstraint(fields=["call", "name"], name="grant_call_document_unique"),
            models.CheckConstraint(condition=~Q(name=""), name="grant_call_document_name"),
        ]

    def __str__(self):
        return self.name


# Estats que ja s'han presentat a l'organisme (RN-M09A-02); «tancada» pot venir d'abans.
SUBMITTED_STATES = ("submitted", "granted", "denied", "justified")


class GrantApplication(models.Model):
    class Status(models.TextChoices):
        DETECTED = "detected", _("Detectada")
        PREPARING = "preparing", _("En preparació")
        SUBMITTED = "submitted", _("Presentada")
        GRANTED = "granted", _("Concedida")
        DENIED = "denied", _("Denegada")
        JUSTIFIED = "justified", _("Justificada")
        CLOSED = "closed", _("Tancada")

    call = models.ForeignKey(
        GrantCall,
        on_delete=models.PROTECT,
        related_name="applications",
        verbose_name=_("convocatòria"),
    )
    status = models.CharField(
        _("estat"), max_length=9, choices=Status.choices, default=Status.DETECTED
    )
    # Amb rol tresorer, junta o administrador (ho comprova el servei).
    responsible = models.ForeignKey(
        "core.Person", on_delete=models.PROTECT, related_name="+", verbose_name=_("responsable")
    )
    department = models.ForeignKey(
        "core.Department", on_delete=models.PROTECT, related_name="+", verbose_name=_("departament")
    )
    cost_centre = models.ForeignKey(
        "treasury.CostCentre",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("centre de cost"),
    )
    # L'import previst en crear-la; el demanat, en presentar-la.
    amount_requested_cents = models.PositiveBigIntegerField(
        _("import demanat"), null=True, blank=True
    )
    submitted_on = models.DateField(_("data de presentació"), null=True, blank=True)
    submission_ref = models.CharField(_("número de registre d'entrada"), max_length=60, blank=True)
    submission_file = _file(_("còpia del que s'ha presentat"))
    expected_response_on = models.DateField(_("resposta prevista"), null=True, blank=True)
    amount_granted_cents = models.PositiveBigIntegerField(
        _("import concedit"), null=True, blank=True
    )
    resolved_on = models.DateField(_("data de la resolució"), null=True, blank=True)
    resolution_file = _file(_("resolució"))
    justified_on = models.DateField(_("data d'enviament de la justificació"), null=True, blank=True)
    justification_extended_to = models.DateField(
        _("pròrroga de la justificació"), null=True, blank=True
    )
    closed_reason = models.TextField(_("motiu del tancament"), blank=True)
    copied_from = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("copiada de"),
    )
    created_by = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, related_name="+", verbose_name=_("creada per")
    )
    created_at = models.DateTimeField(_("creada"), auto_now_add=True)

    class Meta:
        verbose_name = _("sol·licitud d'ajut")
        verbose_name_plural = _("sol·licituds d'ajut")
        constraints = [
            models.CheckConstraint(
                condition=Q(
                    status__in=[
                        "detected",
                        "preparing",
                        "submitted",
                        "granted",
                        "denied",
                        "justified",
                        "closed",
                    ]
                ),
                name="grant_application_status_valid",
            ),
            # RN-M09A-02: presentada (i després) sempre amb data, registre i import demanat.
            models.CheckConstraint(
                condition=~Q(status__in=SUBMITTED_STATES)
                | (
                    Q(submitted_on__isnull=False)
                    & ~Q(submission_ref="")
                    & Q(amount_requested_cents__isnull=False)
                ),
                name="grant_application_submitted_data",
            ),
            # RN-M09A-12: justificada sempre amb la data d'enviament.
            models.CheckConstraint(
                condition=~Q(status="justified") | Q(justified_on__isnull=False),
                name="grant_application_justified_on",
            ),
        ]

    def __str__(self):
        return f"{self.call} ({self.get_status_display()})"


class ApplicationDocument(models.Model):
    """Document d'una sol·licitud: copiat de la convocatòria o afegit, per marcar-lo a punt."""

    application = models.ForeignKey(
        GrantApplication,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name=_("sol·licitud"),
    )
    name = models.CharField(_("document"), max_length=200)
    file = _file(_("fitxer"))
    ready = models.BooleanField(_("a punt"), default=False)
    uploaded_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("pujat per"),
    )

    class Meta:
        verbose_name = _("document de la sol·licitud")
        verbose_name_plural = _("documents de la sol·licitud")
        ordering = ["pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["application", "name"], name="grant_application_document_unique"
            ),
            models.CheckConstraint(condition=~Q(name=""), name="grant_application_document_name"),
        ]

    def __str__(self):
        return self.name


class ApplicationTransition(AppendOnlyModel):
    """Cada canvi d'estat (només INSERT). Un desfer de l'administrador és una transició nova."""

    application = models.ForeignKey(
        GrantApplication,
        on_delete=models.PROTECT,
        related_name="transitions",
        verbose_name=_("sol·licitud"),
    )
    from_status = models.CharField(_("des de"), max_length=9)
    to_status = models.CharField(_("a"), max_length=9)
    reason = models.TextField(_("motiu"), blank=True)
    actor = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, related_name="+", verbose_name=_("qui")
    )
    at = models.DateTimeField(_("quan"), auto_now_add=True)

    class Meta:
        verbose_name = _("transició d'una sol·licitud")
        verbose_name_plural = _("transicions de les sol·licituds")
        ordering = ["pk"]


class DenialNote(AppendOnlyModel):
    """Observació d'una denegació (RN-M09A-13; només INSERT): motiu, data i què millorar. Es
    mostra en copiar la sol·licitud a una convocatòria nova (RN-M09A-14)."""

    application = models.ForeignKey(
        GrantApplication,
        on_delete=models.PROTECT,
        related_name="denial_notes",
        verbose_name=_("sol·licitud"),
    )
    reason = models.TextField(_("motiu"))
    resolved_on = models.DateField(_("data de la resolució"))
    improvements = models.TextField(_("què caldria millorar"))
    recorded_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("registrada per"),
    )
    recorded_at = models.DateTimeField(_("registrada"), auto_now_add=True)

    class Meta:
        verbose_name = _("observació de la denegació")
        verbose_name_plural = _("observacions de la denegació")
        ordering = ["pk"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(reason="") & ~Q(improvements=""), name="grant_denial_note_complete"
            )
        ]


class GrantRequirement(models.Model):
    """Requeriment d'esmena (M09-ajuts-6, T-M09A-15; RN-M09A-19): un esdeveniment de la
    sol·licitud, no un estat. Cada canvi va al registre; canviar `due_on` demana motiu."""

    class Origin(models.TextChoices):
        BODY = "body", _("Organisme")
        CLUB = "club", _("Iniciativa del club")

    application = models.ForeignKey(
        GrantApplication,
        on_delete=models.PROTECT,
        related_name="requirements",
        verbose_name=_("sol·licitud"),
    )
    origin = models.CharField(_("origen"), max_length=4, choices=Origin.choices)
    origin_reason = models.TextField(_("motiu del club"), blank=True)
    received_on = models.DateField(_("rebut o obert el"))
    due_on = models.DateField(_("data límit"))
    description = models.TextField(_("descripció"))
    responsible = models.ForeignKey(
        "core.Person", on_delete=models.PROTECT, related_name="+", verbose_name=_("responsable")
    )
    answered_on = models.DateField(_("respost el"), null=True, blank=True)
    created_by = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, related_name="+", verbose_name=_("creat per")
    )
    created_at = models.DateTimeField(_("creat"), auto_now_add=True)

    class Meta:
        verbose_name = _("requeriment d'esmena")
        verbose_name_plural = _("requeriments d'esmena")
        ordering = ["pk"]
        constraints = [
            models.CheckConstraint(
                condition=Q(origin__in=["body", "club"]), name="grant_requirement_origin"
            ),
            models.CheckConstraint(
                condition=~Q(origin="club", origin_reason=""), name="grant_requirement_club_reason"
            ),
            models.CheckConstraint(
                condition=Q(due_on__gte=F("received_on")), name="grant_requirement_dates"
            ),
            models.CheckConstraint(
                condition=Q(answered_on__isnull=True) | Q(answered_on__gte=F("received_on")),
                name="grant_requirement_answered_after",
            ),
            models.CheckConstraint(condition=~Q(description=""), name="grant_requirement_text"),
        ]

    def __str__(self):
        return f"{self.application_id}: {self.due_on}"


class GrantExpenseLink(models.Model):
    """Despesa lligada a un ajut amb l'import imputat (M09-ajuts-6, T-M09A-09). No s'esborra mai:
    es dona de baixa (`removed_at`). En una sol·licitud justificada, només amb un requeriment obert
    (RN-M09A-21)."""

    application = models.ForeignKey(
        GrantApplication,
        on_delete=models.PROTECT,
        related_name="expense_links",
        verbose_name=_("sol·licitud"),
    )
    expense = models.ForeignKey(
        "expenses.Expense", on_delete=models.PROTECT, related_name="+", verbose_name=_("despesa")
    )
    amount_cents = models.PositiveBigIntegerField(_("import imputat"))
    created_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("lligada per"),
    )
    created_at = models.DateTimeField(_("lligada"), auto_now_add=True)
    removed_at = models.DateTimeField(_("donada de baixa"), null=True, blank=True)
    removed_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("donada de baixa per"),
    )
    # RN-M09A-21: el requeriment amb què s'afegeix o es dona de baixa en una justificada.
    requirement = models.ForeignKey(
        GrantRequirement,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("requeriment"),
    )
    removed_requirement = models.ForeignKey(
        GrantRequirement,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("requeriment de la baixa"),
    )

    class Meta:
        verbose_name = _("despesa lligada a un ajut")
        verbose_name_plural = _("despeses lligades als ajuts")
        ordering = ["pk"]
        constraints = [
            models.CheckConstraint(condition=Q(amount_cents__gt=0), name="grant_link_amount"),
            models.CheckConstraint(
                condition=Q(removed_at__isnull=True, removed_by__isnull=True)
                | Q(removed_at__isnull=False, removed_by__isnull=False),
                name="grant_link_removed_by_whom",
            ),
            models.UniqueConstraint(
                fields=["application", "expense"],
                condition=Q(removed_at__isnull=True),
                name="grant_link_active_unique",
            ),
        ]

    def __str__(self):
        return f"{self.expense_id}: {self.amount_cents} c"
