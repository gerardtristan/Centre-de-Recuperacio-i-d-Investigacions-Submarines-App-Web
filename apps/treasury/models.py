"""Tresoreria, part mínima (M04-6). Cap altra app escriu en aquests models: ho fa amb els
serveis de la 04 (M04-8)."""

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.core.models import Department, UndeletableModel


class TreasuryAccount(UndeletableModel):
    """Compte de tresoreria (HU-T01; RN-T01 a RN-T04): bancari, caixa o trànsit d'un proveïdor
    de cobrament. El saldo no es desa: es calcula a partir dels moviments (RN-T02). Mai l'IBAN
    complet, només els quatre darrers dígits (RN-T03, CA-T01.2). No s'esborra: es desactiva."""

    class Kind(models.TextChoices):
        BANK = "bank", _("Banc")
        CASH = "cash", _("Caixa")
        TRANSIT = "transit", _("Trànsit")

    name = models.CharField(_("nom"), max_length=80, unique=True)
    kind = models.CharField(_("tipus"), max_length=7, choices=Kind.choices)
    # Només als comptes de trànsit: quin proveïdor de cobrament hi deixa els diners. NULL (i no
    # text buit) quan no n'hi ha, com diu M04-6: les restriccions distingeixen «sense valor».
    provider_code = models.CharField(  # noqa: DJ001
        _("proveïdor"), max_length=30, null=True, blank=True
    )
    # Només als comptes bancaris, per reconèixer-los a la pantalla. NULL quan no n'hi ha (M04-6).
    last4 = models.CharField(  # noqa: DJ001
        _("quatre darrers dígits"), max_length=4, null=True, blank=True
    )
    active = models.BooleanField(_("actiu"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("compte de tresoreria")
        verbose_name_plural = _("comptes de tresoreria")
        constraints = [
            models.CheckConstraint(
                condition=Q(kind__in=["bank", "cash", "transit"]),
                name="treasury_account_kind_valid",
            ),
            models.CheckConstraint(
                # `isnull=False` explícit: amb NULL, l'expressió regular donaria «desconegut» i
                # PostgreSQL deixaria passar la restricció.
                condition=(
                    Q(kind="transit")
                    & Q(provider_code__isnull=False)
                    & Q(provider_code__regex=r"^[a-z0-9_]{1,30}$")
                )
                | (~Q(kind="transit") & Q(provider_code__isnull=True)),
                name="treasury_account_provider_only_transit",
            ),
            models.UniqueConstraint(
                fields=["provider_code"],
                condition=Q(kind="transit"),
                name="treasury_account_one_transit_per_provider",
            ),
            models.CheckConstraint(
                condition=Q(last4__isnull=True) | (Q(kind="bank") & Q(last4__regex=r"^[0-9]{4}$")),
                name="treasury_account_last4_only_bank",
            ),
        ]

    def __str__(self):
        return self.name


class CostCentre(UndeletableModel):
    """Centre de cost: el segon nivell d'un departament (HU-T14; RN-T22 i RN-T23; decisió 013).
    La llista la fixa la junta; d'inici només hi ha els de CA-T14.1. No s'esborra: es desactiva,
    i un de desactivat no es pot triar per a càrrecs ni moviments nous (CA-T14.2)."""

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="cost_centres",
        verbose_name=_("departament"),
    )
    name = models.CharField(_("nom"), max_length=80)
    active = models.BooleanField(_("actiu"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("centre de cost")
        verbose_name_plural = _("centres de cost")
        constraints = [
            models.UniqueConstraint(
                fields=["department", "name"], name="cost_centre_unique_in_department"
            ),
            models.CheckConstraint(condition=~Q(name=""), name="cost_centre_name_not_empty"),
        ]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self) -> str:
        """«General / Quotes de socis» (CA-T14.1)."""
        return f"{self.department.name} / {self.name}"

    @classmethod
    def selectable(cls):
        """Els que es poden triar per a un càrrec o un moviment nou (CA-T14.2): actius i d'un
        departament actiu."""
        return cls.objects.filter(active=True, department__active=True).select_related("department")
