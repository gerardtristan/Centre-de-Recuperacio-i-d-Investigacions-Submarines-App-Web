from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import AppendOnlyModel


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
    # El moviment `expense` de la 04; el posa `services.pay` (T-M09-05).
    paid_movement = models.OneToOneField(
        "treasury.Movement",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("moviment del pagament"),
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
            # Pagada sempre amb el seu moviment; per pagar, mai.
            models.CheckConstraint(
                condition=~models.Q(status="paid", paid_movement__isnull=True)
                & ~models.Q(status="to_pay", paid_movement__isnull=False),
                name="expense_paid_has_movement",
            ),
            models.UniqueConstraint(
                fields=["supplier", "invoice_number"],
                condition=~models.Q(invoice_number=""),
                name="expense_invoice_number_unique_per_supplier",
            ),
        ]

    def __str__(self):
        return f"{self.description} ({self.amount_cents} c)"


class ExpenseAnnulment(AppendOnlyModel):
    """Anul·lació d'una despesa (M09-6, RN-M09-11): només INSERT. Si estava pagada, porta el
    contramoviment de la 04."""

    expense = models.OneToOneField(
        Expense, on_delete=models.PROTECT, related_name="annulment", verbose_name=_("despesa")
    )
    reason = models.TextField(_("motiu"))
    reversal_movement = models.OneToOneField(
        "treasury.Movement",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("contramoviment"),
    )
    annulled_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("anul·lada per"),
    )
    annulled_at = models.DateTimeField(_("anul·lada"), auto_now_add=True)

    class Meta:
        verbose_name = _("anul·lació d'una despesa")
        verbose_name_plural = _("anul·lacions de despeses")
        constraints = [
            models.CheckConstraint(condition=~models.Q(reason=""), name="expense_annulment_reason")
        ]


class OtherIncome(models.Model):
    """Ingrés que no és un càrrec: ajut, patrocini, donatiu o un altre (M09-6, T-M09-08). Compta
    al departament i, si cal, al projecte; un ajut mai a una activitat (RN-M09-08). L'activitat i
    el projecte (02) i la sol·licitud d'ajut (apartat d'ajuts) s'afegeixen amb els seus mòduls."""

    class Kind(models.TextChoices):
        GRANT = "grant", _("Ajut")
        SPONSORSHIP = "sponsorship", _("Patrocini")
        DONATION = "donation", _("Donatiu")
        OTHER = "other", _("Un altre")

    kind = models.CharField(_("tipus"), max_length=11, choices=Kind.choices)
    # Organisme o empresa. Donatius de persones: només anònims fins a la gestoria (S-M09-03).
    payer = models.CharField(_("pagador"), max_length=140)
    amount_cents = models.PositiveBigIntegerField(_("import (cèntims)"))
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
    # Resolució o contracte; obligatori en un ajut.
    document_file = models.ForeignKey(
        "core.PrivateFile",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("resolució o contracte"),
    )
    movement = models.OneToOneField(
        "treasury.Movement", on_delete=models.PROTECT, related_name="+", verbose_name=_("moviment")
    )
    recorded_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("registrat per"),
    )
    recorded_at = models.DateTimeField(_("registrat"), auto_now_add=True)

    class Meta:
        verbose_name = _("altre ingrés")
        verbose_name_plural = _("altres ingressos")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount_cents__gt=0), name="other_income_amount_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(kind__in=["grant", "sponsorship", "donation", "other"]),
                name="other_income_kind_valid",
            ),
            models.CheckConstraint(
                condition=~models.Q(kind="grant", document_file__isnull=True),
                name="other_income_grant_has_document",
            ),
        ]

    def __str__(self):
        return f"{self.get_kind_display()} ({self.amount_cents} c)"
