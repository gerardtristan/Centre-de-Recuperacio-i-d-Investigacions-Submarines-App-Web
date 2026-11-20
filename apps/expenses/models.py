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
