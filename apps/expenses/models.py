from django.db import models
from django.utils.translation import gettext_lazy as _


class ExpenseCategory(models.Model):
    """Categoria de despesa (M09-6, T-M09-03): una dada que s'amplia des de l'app (VC-33). Les
    inicials (F §7) les posa la migració."""

    name = models.CharField(_("nom"), max_length=80, unique=True)
    active = models.BooleanField(_("activa"), default=True)

    class Meta:
        verbose_name = _("categoria de despesa")
        verbose_name_plural = _("categories de despesa")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Supplier(models.Model):
    """Proveïdor (M09-6): només el nom i el NIF o CIF de la factura. Sense adreça, telèfon ni
    compte bancari (M09-12)."""

    name = models.CharField(_("nom"), max_length=140)
    tax_id = models.CharField(_("NIF o CIF"), max_length=20, blank=True)
    active = models.BooleanField(_("actiu"), default=True)

    class Meta:
        verbose_name = _("proveïdor")
        verbose_name_plural = _("proveïdors")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Expense(models.Model):
    """Despesa amb factura (M09-6, T-M09-04). Una despesa pagada o anul·lada no es modifica:
    s'anul·la amb motiu i se'n registra una de nova (RN-M09-11). Pagar i anul·lar: T-M09-05; la
    còpia emmascarada i la marca «il·legible» dels documents: T-M09-25."""

    class Status(models.TextChoices):
        TO_PAY = "to_pay", _("Per pagar")
        PAID = "paid", _("Pagada")
        ANNULLED = "annulled", _("Anul·lada")

    supplier = models.ForeignKey(
        Supplier, on_delete=models.PROTECT, related_name="expenses", verbose_name=_("proveïdor")
    )
    invoice_number = models.CharField(_("número de factura"), max_length=40, blank=True)
    invoice_date = models.DateField(_("data de la factura"))
    category = models.ForeignKey(
        ExpenseCategory, on_delete=models.PROTECT, related_name="+", verbose_name=_("categoria")
    )
    # Sense dades de persones (M09-6).
    description = models.CharField(_("descripció"), max_length=200)
    amount_cents = models.PositiveBigIntegerField(_("import (cèntims)"))
    tax_cents = models.PositiveBigIntegerField(_("IVA (cèntims)"), null=True, blank=True)
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
    # Sense factura, la despesa és «sense factura» (RN-M09-09).
    invoice_file = models.ForeignKey(
        "core.PrivateFile",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("factura"),
    )
    status = models.CharField(
        _("estat"), max_length=8, choices=Status.choices, default=Status.TO_PAY
    )
    recorded_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("registrada per"),
    )
    recorded_at = models.DateTimeField(_("registrada"), auto_now_add=True)
    updated_at = models.DateTimeField(_("modificada"), auto_now=True)

    class Meta:
        verbose_name = _("despesa")
        verbose_name_plural = _("despeses")
        ordering = ["-invoice_date", "-pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount_cents__gt=0), name="expense_amount_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["to_pay", "paid", "annulled"]),
                name="expense_status_valid",
            ),
            models.UniqueConstraint(
                fields=["supplier", "invoice_number"],
                condition=~models.Q(invoice_number=""),
                name="expense_invoice_number_unique_per_supplier",
            ),
        ]

    def __str__(self):
        return f"{self.description} ({self.amount_cents} c)"
