"""Factures i rectificatives (M09-6, T-M09-19 i T-M09-20). El número, el PDF i el QR els dona el
servei homologat (RN-M09-17); una factura emesa no s'edita ni s'esborra mai (RN-M09-18). El PDF
és un lligam a un fitxer privat de la 00 que ompliran les vistes (T-M09-21)."""

from django.db import models
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _


class Invoice(models.Model):
    class Series(models.TextChoices):
        ORDINARY = "F", _("Ordinària")
        RECTIFYING = "R", _("Rectificativa")

    class Status(models.TextChoices):
        REQUESTED = "requested", _("Demanada")
        ISSUED = "issued", _("Emesa")
        FAILED = "failed", _("Fallida")

    series = models.CharField(_("sèrie"), max_length=1, choices=Series.choices)
    number = models.CharField(_("número"), max_length=40, blank=True)
    issued_on = models.DateField(_("data d'emissió"), null=True, blank=True)
    customer_person = models.ForeignKey(
        "core.Person",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("client (persona)"),
    )
    customer_name = models.CharField(_("client (empresa)"), max_length=140, blank=True)
    customer_tax_id = models.CharField(_("NIF o CIF del client"), max_length=20, blank=True)
    base_cents = models.PositiveBigIntegerField(_("base (cèntims)"))
    tax_cents = models.PositiveBigIntegerField(_("IVA (cèntims)"))
    total_cents = models.PositiveBigIntegerField(_("total (cèntims)"))
    charge = models.ForeignKey(
        "core.Charge",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("càrrec"),
    )
    rectifies = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="rectifications",
        verbose_name=_("rectifica"),
    )
    refund_movement = models.OneToOneField(
        "treasury.Movement",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("devolució"),
    )
    provider_ref = models.CharField(_("referència del servei"), max_length=80, blank=True)
    pdf_file = models.ForeignKey(
        "core.PrivateFile",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("PDF"),
    )
    qr_payload = models.TextField(_("QR"), blank=True)
    status = models.CharField(
        _("estat"), max_length=9, choices=Status.choices, default=Status.REQUESTED
    )
    attempts = models.PositiveSmallIntegerField(_("intents"), default=0)
    created_at = models.DateTimeField(_("creada"), auto_now_add=True)

    class Meta:
        verbose_name = _("factura")
        verbose_name_plural = _("factures")
        ordering = ["pk"]
        constraints = [
            models.CheckConstraint(condition=Q(series__in=["F", "R"]), name="invoice_series"),
            models.CheckConstraint(
                condition=Q(status__in=["requested", "issued", "failed"]), name="invoice_status"
            ),
            models.CheckConstraint(
                condition=Q(total_cents=F("base_cents") + F("tax_cents")), name="invoice_total"
            ),
            # RN-M09-18: una rectificativa sempre diu quina factura rectifica; una ordinària, mai.
            models.CheckConstraint(
                condition=Q(series="R", rectifies__isnull=False)
                | Q(series="F", rectifies__isnull=True),
                name="invoice_rectifies_only_r",
            ),
            models.CheckConstraint(
                condition=~Q(status="issued") | (~Q(number="") & Q(issued_on__isnull=False)),
                name="invoice_issued_has_number",
            ),
            models.UniqueConstraint(
                fields=["series", "number"], condition=~Q(number=""), name="invoice_number_unique"
            ),
            # RN-M09-17: un càrrec té com a màxim una factura ordinària.
            models.UniqueConstraint(
                fields=["charge"],
                condition=Q(series="F", charge__isnull=False),
                name="invoice_one_per_charge",
            ),
        ]

    def __str__(self):
        return f"{self.series} {self.number or self.pk}"


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="lines", verbose_name=_("factura")
    )
    description = models.CharField(_("descripció"), max_length=200)
    quantity = models.PositiveIntegerField(_("quantitat"))
    unit_cents = models.PositiveBigIntegerField(_("preu unitari (cèntims)"))
    # El tipus d'IVA per tipus de càrrec és de la T-M09-27 [A verificar: gestoria].
    total_cents = models.PositiveBigIntegerField(_("total (cèntims)"))

    class Meta:
        verbose_name = _("línia de factura")
        verbose_name_plural = _("línies de factura")
        ordering = ["pk"]
        constraints = [
            models.CheckConstraint(
                condition=Q(total_cents=F("quantity") * F("unit_cents")), name="invoice_line_total"
            ),
            models.CheckConstraint(condition=Q(quantity__gt=0), name="invoice_line_quantity"),
        ]

    def __str__(self):
        return self.description
