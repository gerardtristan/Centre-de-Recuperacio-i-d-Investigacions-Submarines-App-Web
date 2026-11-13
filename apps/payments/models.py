"""Models dels pagaments (M05a-6 i M05b-6). Cap camp amb dades de targeta ni cap IBAN en aquest
fitxer."""

import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from apps.core.models import Charge, UndeletableModel, UndeletableQuerySet, validate_cents


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


class AttemptLocked(Exception):
    """El que identifica un intent (càrrec, mètode, import, clau, qui l'ha iniciat) no canvia
    mai, i no hi ha canvis ni altes en bloc."""


class InvalidTransition(Exception):
    """Canvi d'estat que RN-M05b-03 no permet."""


class AttemptMethod(models.TextChoices):
    CARD = "card", _("Targeta")
    BIZUM = "bizum", _("Bizum")
    TRANSFER = "transfer", _("Transferència")
    DIRECT_DEBIT = "direct_debit", _("Domiciliació")
    SAVED_CARD = "saved_card", _("Targeta guardada")


class AttemptStatus(models.TextChoices):
    CREATED = "created", _("Creat")
    IN_PROGRESS = "in_progress", _("En curs")
    SENT_TO_BANK = "sent_to_bank", _("Enviat al banc")
    PAID = "paid", _("Pagat")
    FAILED = "failed", _("Fallit")
    EXPIRED = "expired", _("Caducat")
    ABANDONED = "abandoned", _("Abandonat")
    TO_REVIEW = "to_review", _("A revisar")
    CANCELLED = "cancelled", _("Cancel·lat")


# RN-M05b-03, sencera. «Pagat» no torna enrere: les correccions són devolucions o retorns. El
# que la regla no preveu (una confirmació tardana, sortir d'«a revisar», entrar a «cancel·lat»)
# no hi és mentre no es respongui la P-78.
ATTEMPT_TRANSITIONS = frozenset(
    (old, new)
    for old, targets in {
        "created": ("in_progress", "sent_to_bank"),
        "in_progress": ("paid", "failed", "expired", "abandoned", "to_review"),
        "sent_to_bank": ("paid", "failed"),
    }.items()
    for new in targets
)


class PaymentAttemptQuerySet(UndeletableQuerySet):
    def update(self, **kwargs):
        """Cap canvi en bloc: l'estat canvia fila a fila, amb `attempts.transition`."""
        raise AttemptLocked

    def bulk_create(self, *args, **kwargs):
        """Cap alta en bloc: cada intent pren l'import del seu càrrec en desar-se."""
        raise AttemptLocked


class PaymentAttempt(UndeletableModel):
    """Intent de pagament d'un càrrec (M05b-6; T-M05b-03). Un càrrec en pot tenir diversos; com
    a molt un d'en curs i com a molt un de pagat (RN-M05b-04, a la base de dades).

    Es crea i canvia d'estat amb `apps.payments.attempts`. Cap dada de targeta, cap IBAN i cap
    referència al mandat: qui lligarà l'intent amb el mandat és el rebut domiciliat, a la
    llesca de la domiciliació."""

    Method = AttemptMethod
    Status = AttemptStatus
    # No canvien mai després de crear l'intent.
    IDENTITY_FIELDS = frozenset(
        {"charge_id", "method", "amount_cents", "idempotency_key", "guest_link_id", "started_by_id"}
    )

    objects = PaymentAttemptQuerySet.as_manager()

    charge = models.ForeignKey(
        Charge, on_delete=models.PROTECT, related_name="attempts", verbose_name=_("càrrec")
    )
    method = models.CharField(_("mètode"), max_length=12, choices=Method.choices)
    # RN-M05b-02: és l'import del càrrec en crear l'intent; mai ve de fora.
    amount_cents = models.PositiveBigIntegerField(_("import (cèntims)"))
    status = models.CharField(
        _("estat"), max_length=12, choices=Status.choices, default=Status.CREATED
    )
    # Buits fins que el proveïdor crea l'ordre.
    provider_code = models.CharField(_("proveïdor"), max_length=30, blank=True)
    provider_order_id = models.CharField(_("ordre del proveïdor"), max_length=100, blank=True)
    idempotency_key = models.UUIDField(
        _("clau d'idempotència"), default=uuid.uuid4, unique=True, editable=False
    )
    expires_at = models.DateTimeField(_("caduca el"), null=True, blank=True)
    guest_link = models.ForeignKey(
        "core.GuestLink",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("enllaç de convidat"),
    )
    # Null: l'ha iniciat un convidat o el sistema.
    started_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("iniciat per"),
    )
    review_reason = models.TextField(_("motiu de la revisió"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("intent de pagament")
        verbose_name_plural = _("intents de pagament")
        constraints = [
            models.CheckConstraint(
                condition=Q(amount_cents__gt=0), name="payment_attempt_amount_positive"
            ),
            models.CheckConstraint(
                condition=Q(method__in=AttemptMethod.values), name="payment_attempt_method_valid"
            ),
            models.CheckConstraint(
                condition=Q(status__in=AttemptStatus.values), name="payment_attempt_status_valid"
            ),
            models.CheckConstraint(
                condition=~Q(status="to_review") | ~Q(review_reason=""),
                name="payment_attempt_review_has_reason",
            ),
            # RN-M05b-04: un sol intent en curs (o enviat al banc) i un sol «pagat» per càrrec.
            models.UniqueConstraint(
                fields=["charge"],
                condition=Q(status__in=["in_progress", "sent_to_bank"]),
                name="payment_attempt_one_in_progress",
            ),
            models.UniqueConstraint(
                fields=["charge"], condition=Q(status="paid"), name="payment_attempt_one_paid"
            ),
            models.UniqueConstraint(
                fields=["provider_code", "provider_order_id"],
                condition=~Q(provider_order_id=""),
                name="payment_attempt_provider_order_once",
            ),
        ]

    def __str__(self):
        return f"{self.get_method_display()} {self.amount_cents} c ({self.get_status_display()})"

    def check_transition(self, old: str, new: str) -> None:
        """RN-M05b-03. Només una domiciliació s'envia al banc: una targeta no hi arriba mai."""
        to_bank = new == self.Status.SENT_TO_BANK and self.method != self.Method.DIRECT_DEBIT
        if (old, new) not in ATTEMPT_TRANSITIONS or to_bank:
            raise InvalidTransition(f"{old} → {new}")

    def save(self, *args, update_fields=None, **kwargs):
        if self._state.adding:
            if self.status != self.Status.CREATED:  # RN-M05b-03: tot intent neix «creat»
                raise InvalidTransition(f"— → {self.status}")
            validate_cents(self.amount_cents)
            if self.amount_cents != self.charge.amount_cents:
                raise ValidationError(gettext("L'import de l'intent ha de ser el del càrrec."))
        else:
            # Es compara el que s'escriurà amb el que hi ha desat, no amb la còpia en memòria.
            names = self.IDENTITY_FIELDS | {"status"}
            if update_fields is not None:
                names &= {self._meta.get_field(name).attname for name in update_fields}
            stored = type(self).objects.values(*names).get(pk=self.pk) if names else {}
            changed = {name for name in names if getattr(self, name) != stored[name]}
            if changed - {"status"}:
                raise AttemptLocked
            if changed:
                self.check_transition(stored["status"], self.status)
        super().save(*args, update_fields=update_fields, **kwargs)
