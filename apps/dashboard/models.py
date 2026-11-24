"""Preferència d'ordre del dashboard per compte (T-M08-12; M08-6; P-490, decisió 105).

És una preferència, no una dada de negoci: no passa pel registre d'activitat. És l'única
escriptura del dashboard (RN-M08-06), i només la fa `layout.save` per al mateix compte."""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class DashboardLayout(models.Model):
    account = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("compte"),
    )
    order = models.JSONField(_("ordre dels blocs"), default=list)  # codis del catàleg
    hidden = models.JSONField(_("blocs amagats"), default=list)  # codis del catàleg
    updated_at = models.DateTimeField(_("actualitzat el"), auto_now=True)

    class Meta:
        verbose_name = _("ordre del dashboard")
        verbose_name_plural = _("ordres del dashboard")

    def __str__(self):
        return f"{self.account_id}"
