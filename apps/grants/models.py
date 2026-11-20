"""Ajuts: convocatòria, documents requerits i sol·licitud (M09-ajuts-6, T-M09A-02). Cap dada
personal de socis ni participants (RN-M09A-15): només el responsable i qui fa cada acció.

Els fitxers (bases, còpia presentada, resolució, documents) són només un lligam a un fitxer
privat de la 00: pujar-los, xifrar-los i qui els obre és de la T-M09-25 (051). La denegació, els
requeriments, les despeses lligades, els paquets i els avisos arriben amb les seves tasques."""

from django.db import models
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _


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
