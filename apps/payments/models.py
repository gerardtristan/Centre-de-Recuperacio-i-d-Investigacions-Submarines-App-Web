"""Models dels pagaments (M05a-6). Cap camp amb dades de targeta ni cap IBAN en aquest fitxer."""

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.core.models import UndeletableModel, UndeletableQuerySet


class ProviderEventLocked(Exception):
    """Una notificació desada no es modifica: només se'n tanca el resultat, una vegada."""


class ProviderEventQuerySet(UndeletableQuerySet):
    def update(self, **kwargs):
        """Cap canvi en bloc: el resultat es tanca fila a fila, amb `save(update_fields=...)`."""
        raise ProviderEventLocked


class ProviderEvent(UndeletableModel):
    """Notificació rebuda del proveïdor (arquitectura §4.2; T-M05a-04). Només s'hi afegeixen
    files; d'una fila només canvien, una sola vegada, el resultat i la data de processament.

    No es desa el cos de la notificació, només la seva empremta i els camps normalitzats que
    calen per processar-la (ordre, estat, import i moneda): cap dada personal ni de targeta."""

    class Result(models.TextChoices):
        RECEIVED = "received", _("Rebuda, per processar")
        PROCESSED = "processed", _("Processada")
        IGNORED_DUPLICATE = "ignored_duplicate", _("Repetida, ignorada")
        REJECTED_SIGNATURE = "rejected_signature", _("Rebutjada: firma o origen no vàlids")
        TO_REVIEW = "to_review", _("A revisar")
        ERROR = "error", _("Error")

    CLOSABLE_FIELDS = frozenset({"result", "processed_at"})

    objects = ProviderEventQuerySet.as_manager()

    provider_code = models.CharField(_("proveïdor"), max_length=30)
    # Buit quan la notificació no s'ha pogut llegir (rebutjada o incomprensible).
    external_id = models.CharField(_("identificador de l'esdeveniment"), max_length=100, blank=True)
    event_type = models.CharField(_("tipus"), max_length=60, blank=True)
    payload_hash = models.CharField(_("empremta del cos"), max_length=64)
    order_id = models.CharField(_("ordre del proveïdor"), max_length=100, blank=True)
    amount_cents = models.PositiveBigIntegerField(_("import (cèntims)"), null=True, blank=True)
    currency = models.CharField(_("moneda"), max_length=3, blank=True)
    received_at = models.DateTimeField(_("rebuda"), auto_now_add=True)
    processed_at = models.DateTimeField(_("processada"), null=True, blank=True)
    result = models.CharField(
        _("resultat"), max_length=20, choices=Result.choices, default=Result.RECEIVED
    )

    class Meta:
        verbose_name = _("notificació del proveïdor")
        verbose_name_plural = _("notificacions del proveïdor")
        constraints = [
            models.CheckConstraint(
                condition=Q(
                    result__in=[
                        "received",
                        "processed",
                        "ignored_duplicate",
                        "rejected_signature",
                        "to_review",
                        "error",
                    ]
                ),
                name="provider_event_result_valid",
            ),
            # Idempotència (§4.2, punt 2): un esdeveniment del proveïdor s'accepta una sola
            # vegada. Una repetició o un rebuig no ocupen l'identificador de l'original.
            models.UniqueConstraint(
                fields=["provider_code", "external_id"],
                condition=~Q(result__in=["ignored_duplicate", "rejected_signature"])
                & ~Q(external_id=""),
                name="provider_event_accepted_once",
            ),
        ]
        indexes = [models.Index(fields=["result", "received_at"], name="provider_event_result_idx")]

    def __str__(self):
        return f"{self.provider_code} {self.external_id or '—'} ({self.get_result_display()})"

    def save(self, *args, update_fields=None, **kwargs):
        if not self._state.adding:
            stored = type(self).objects.values_list("result", flat=True).get(pk=self.pk)
            fields = set(update_fields or ())
            if stored != self.Result.RECEIVED or not fields or not fields <= self.CLOSABLE_FIELDS:
                raise ProviderEventLocked
        super().save(*args, update_fields=update_fields, **kwargs)
