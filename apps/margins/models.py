from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateRangeField, RangeOperators
from django.db import models
from django.db.models import F, Func, Q, Value
from django.utils.translation import gettext_lazy as _

from apps.core.models import AppendOnlyModel


class DateRange(Func):
    function = "DATERANGE"
    output_field = DateRangeField()


class Period(models.Model):
    """Període del 09 (M09-6). El tancament, la reobertura i la llista de control (PeriodEvent)
    arriben amb la T-M09-16; aquí només hi ha el que necessita la guarda de la 04 (T-M09-02)."""

    class Status(models.TextChoices):
        OPEN = "open", _("Obert")
        CLOSED = "closed", _("Tancat")

    starts_on = models.DateField(_("comença"))
    ends_on = models.DateField(_("acaba"))
    status = models.CharField(_("estat"), max_length=6, choices=Status.choices, default="open")

    class Meta:
        verbose_name = _("període")
        verbose_name_plural = _("períodes")
        ordering = ["starts_on"]
        constraints = [
            models.CheckConstraint(
                condition=Q(ends_on__gte=F("starts_on")), name="margins_period_dates_in_order"
            ),
            models.CheckConstraint(
                condition=Q(status__in=["open", "closed"]), name="margins_period_status_valid"
            ),
            # Sense solapaments (M09-6): cap dia dins de dos períodes.
            ExclusionConstraint(
                name="margins_period_no_overlap",
                expressions=[
                    (DateRange("starts_on", "ends_on", Value("[]")), RangeOperators.OVERLAPS)
                ],
            ),
        ]

    def __str__(self):
        return f"{self.starts_on} – {self.ends_on}"


class PlannedCost(models.Model):
    """Cost previst d'una activitat per categoria de despesa (M09-6, T-M09-09). Compta al marge
    previst només mentre la categoria no té costos reals (RN-M09-06). Es pot canviar mentre
    l'activitat no és tancada; cada canvi va al registre."""

    activity = models.ForeignKey(
        "activities.Activity",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("activitat"),
    )
    category = models.ForeignKey(
        "expenses.ExpenseCategory",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("categoria"),
    )
    amount_cents = models.PositiveBigIntegerField(_("import previst (cèntims)"))
    note = models.CharField(_("nota"), max_length=200, blank=True)
    created_by = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, related_name="+", verbose_name=_("creat per")
    )
    created_at = models.DateTimeField(_("creat"), auto_now_add=True)

    class Meta:
        verbose_name = _("cost previst")
        verbose_name_plural = _("costos previstos")
        constraints = [
            models.UniqueConstraint(
                fields=["activity", "category"], name="margins_planned_cost_unique"
            )
        ]

    def __str__(self):
        return f"{self.category}: {self.amount_cents} c"


class MarginSnapshot(AppendOnlyModel):
    """Marge real congelat en tancar una activitat (M09-6; RN-M09-07; T-M09-12). Només INSERT: un
    moviment posterior no el canvia, surt com a «ajust posterior». Vigent = el que no és substituït
    (`supersedes`, quan es reobri un període, T-M09-16)."""

    activity = models.ForeignKey(
        "activities.Activity",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("activitat"),
    )
    income_enrolments_cents = models.BigIntegerField(_("inscripcions (cèntims)"))
    other_direct_income_cents = models.BigIntegerField(_("altres ingressos directes (cèntims)"))
    direct_costs_cents = models.BigIntegerField(_("costos directes (cèntims)"))
    material_cost_cents = models.BigIntegerField(_("cost de material (cèntims)"))
    margin_cents = models.BigIntegerField(_("marge (cèntims)"))  # amb signe
    margin_pct_tenths = models.IntegerField(_("marge (dècimes de punt)"), null=True, blank=True)
    participants = models.PositiveIntegerField(_("participants"))
    breakdown = models.JSONField(_("detall"))
    closed_by = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, related_name="+", verbose_name=_("tancat per")
    )
    closed_at = models.DateTimeField(_("tancat el"))
    supersedes = models.OneToOneField(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="superseded_by",
        verbose_name=_("substitueix"),
    )
    reopen_reason = models.TextField(_("motiu de la reobertura"), blank=True)

    class Meta:
        verbose_name = _("marge congelat")
        verbose_name_plural = _("marges congelats")
        ordering = ["-closed_at", "-pk"]
        constraints = [
            models.CheckConstraint(
                condition=Q(supersedes__isnull=True) | ~Q(reopen_reason=""),
                name="margins_snapshot_superseding_needs_reason",
            )
        ]

    def __str__(self):
        return f"{self.activity_id}: {self.margin_cents} c"
