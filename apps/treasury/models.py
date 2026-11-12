"""Tresoreria, part mínima (M04-6). Cap altra app escriu en aquests models: ho fa amb els
serveis de la 04 (M04-8)."""

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.core.models import UndeletableModel


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
