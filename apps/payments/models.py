"""Models dels pagaments (M05a-6 i M05b-6). Cap camp amb dades de targeta. L'IBAN només és a
`MandateBankAccount.iban_ciphertext`, xifrat (044)."""

import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    AppendOnlyModel,
    Charge,
    UndeletableModel,
    UndeletableQuerySet,
    validate_cents,
)


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
# no hi és mentre no es respongui la P-82.
ATTEMPT_TRANSITIONS = frozenset(
    (old, new)
    for old, targets in {
        "created": ("in_progress", "sent_to_bank"),
        "in_progress": ("paid", "failed", "expired", "abandoned", "to_review"),
        "sent_to_bank": ("paid", "failed"),
    }.items()
    for new in targets
)
# 045 (T-M05b-29): una transferència conciliada amb el càrrec equivocat. L'intent pagat queda
# «cancel·lat» (P-122) perquè el càrrec, que torna a pendent, es pugui tornar a pagar. El mateix
# per a un rebut domiciliat que el banc retorna (T-M05b-12, P-290).
REVERT_TRANSFER = ("paid", "cancelled")


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
        {
            "charge_id",
            "method",
            "amount_cents",
            "idempotency_key",
            "guest_link_id",
            "started_by_id",
            "ui_timeout_minutes",
        }
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
    # Bizum: els minuts que la pantalla l'espera, desats en obrir-lo (VC-17, RN-M05b-24).
    ui_timeout_minutes = models.PositiveSmallIntegerField(
        _("minuts d'espera a la pantalla"), null=True, blank=True
    )
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
        revert = (old, new) == REVERT_TRANSFER and self.method in (
            self.Method.TRANSFER,
            self.Method.DIRECT_DEBIT,
        )
        if ((old, new) not in ATTEMPT_TRANSITIONS and not revert) or to_bank:
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


class ReceiptLocked(Exception):
    """Un rebut emès no canvia: el número i l'intent queden fixats (RN-M05b-19)."""


class ReceiptCounter(models.Model):
    """Últim número de rebut de cada any (RN-M05b-19). Com el comptador del número de soci, no
    és una seqüència de PostgreSQL, que consumiria números en desfer una transacció: el servei
    l'avança amb `SELECT … FOR UPDATE` dins la mateixa transacció que emet el rebut, i així no
    queda cap forat."""

    year = models.PositiveSmallIntegerField(_("any"), unique=True)
    last_number = models.PositiveIntegerField(_("últim número"), default=0)

    class Meta:
        verbose_name = _("comptador de rebuts")
        verbose_name_plural = _("comptadors de rebuts")

    def __str__(self):
        return f"{self.year}: {self.last_number}"


class ReceiptQuerySet(UndeletableQuerySet):
    def update(self, **kwargs):
        raise ReceiptLocked


class Receipt(UndeletableModel):
    """Rebut d'un intent pagat (M05b-6; T-M05b-07). És un rebut, no una factura (P-47). El
    concepte, l'import, el departament i el mètode surten del càrrec i de l'intent: no es
    copien. Es crea amb `apps.payments.receipts.issue`."""

    objects = ReceiptQuerySet.as_manager()

    attempt = models.OneToOneField(
        PaymentAttempt, on_delete=models.PROTECT, related_name="receipt", verbose_name=_("intent")
    )
    number = models.CharField(_("número"), max_length=20, unique=True)
    # L'any del número és el de l'emissió, en hora local: el servei passa la mateixa hora.
    issued_at = models.DateTimeField(_("emès"), default=timezone.now, editable=False)

    class Meta:
        verbose_name = _("rebut")
        verbose_name_plural = _("rebuts")

    def __str__(self):
        return self.number

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ReceiptLocked
        super().save(*args, **kwargs)


class ReceiptCancellation(AppendOnlyModel):
    """Anul·lació d'un rebut (M05b-6: «anul·la el rebut amb una nota, no l'esborra»; 045). El
    rebut no es toca: una fila nova diu que ja no val. Només INSERT, també a la base de dades
    (migració 0008)."""

    receipt = models.OneToOneField(
        Receipt, on_delete=models.PROTECT, related_name="cancellation", verbose_name=_("rebut")
    )
    note = models.TextField(_("nota"))
    cancelled_at = models.DateTimeField(_("data de l'anul·lació"), auto_now_add=True)

    class Meta:
        verbose_name = _("anul·lació de rebut")
        verbose_name_plural = _("anul·lacions de rebut")
        constraints = [
            models.CheckConstraint(
                condition=Q(note__regex=r"\S"), name="receipt_cancellation_note_required"
            ),
        ]

    def __str__(self):
        return f"{self._meta.verbose_name} {self.receipt_id}"


# 05a: mètode de pagament de la quota i mandats SEPA (T-M05a-08; M05a-6; decisió 044).

MANDATE_REFERENCE = r"^CRIS[0-9]{6}M[0-9]{2}$"  # RN-M05a-03


class FeeMethod(models.TextChoices):
    DIRECT_DEBIT = "direct_debit", _("domiciliació")
    SAVED_CARD = "saved_card", _("targeta guardada")
    PAY_EACH_TIME = "pay_each_time", _("pagar cada vegada")


class SavedCardStatus(models.TextChoices):
    ACTIVE = "active", _("activa")
    REMOVED = "removed", _("esborrada")
    EXPIRED = "expired", _("caducada")


class SavedCard(models.Model):
    """Targeta guardada al proveïdor (RN-M05a-10; condicional a la P-45, punt 6): només la
    referència del proveïdor i el que es mostra. Mai el número ni el codi de seguretat."""

    Status = SavedCardStatus

    person = models.ForeignKey("core.Person", on_delete=models.PROTECT, related_name="+")
    provider_code = models.CharField(_("proveïdor"), max_length=30)
    provider_card_id = models.CharField(_("identificador del proveïdor"), max_length=100)
    last4 = models.CharField(_("quatre darrers dígits"), max_length=4)
    expiry_month = models.PositiveSmallIntegerField(_("mes de caducitat"), null=True, blank=True)
    expiry_year = models.PositiveSmallIntegerField(_("any de caducitat"), null=True, blank=True)
    status = models.CharField(
        _("estat"), max_length=10, choices=Status.choices, default=Status.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("targeta guardada")
        verbose_name_plural = _("targetes guardades")
        constraints = [
            models.UniqueConstraint(
                fields=["provider_code", "provider_card_id"], name="saved_card_unique_provider_id"
            ),
            models.CheckConstraint(
                condition=Q(status__in=SavedCardStatus.values), name="saved_card_status_valid"
            ),
            models.CheckConstraint(
                condition=Q(last4__regex=r"^[0-9]{4}$"), name="saved_card_last4_digits"
            ),
            models.CheckConstraint(
                condition=Q(expiry_month__isnull=True)
                | Q(expiry_month__gte=1, expiry_month__lte=12),
                name="saved_card_expiry_month_valid",
            ),
        ]

    def __str__(self):
        return f"… {self.last4}"


class MandateStatus(models.TextChoices):
    ACTIVE = "active", _("actiu")
    REVOKED = "revoked", _("revocat")
    EXPIRED = "expired", _("caducat")
    BLOCKED = "blocked", _("bloquejat")


class SepaMandate(UndeletableModel):
    """Mandat SEPA d'un soci (M05a-6). Un sol mandat actiu per soci (RN-M05a-02). L'IBAN no és
    aquí: és a `MandateBankAccount`, xifrat. Es crea amb `apps.payments.mandates`."""

    Status = MandateStatus
    REPLACED = "substituït"  # motiu de RN-M05a-02

    member = models.ForeignKey("members.Member", on_delete=models.PROTECT, related_name="+")
    reference = models.CharField(_("referència"), max_length=35, unique=True)
    holder_name = models.CharField(_("titular del compte"), max_length=70)
    holder_is_member = models.BooleanField(_("el titular és el soci"))
    signed_at = models.DateTimeField(_("signat el"))
    sequence_type = models.CharField(_("tipus"), max_length=10, default="recurrent")
    creditor_identifier = models.CharField(_("identificador de creditor"), max_length=35)
    legal_text = models.ForeignKey("core.LegalText", on_delete=models.PROTECT, related_name="+")
    signed_by_account = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, related_name="+"
    )
    evidence = models.JSONField(_("prova de la signatura"), default=dict)
    status = models.CharField(
        _("estat"), max_length=10, choices=Status.choices, default=Status.ACTIVE
    )
    revoked_at = models.DateTimeField(_("revocat el"), null=True, blank=True)
    revoked_reason = models.CharField(_("motiu de la revocació"), max_length=200, blank=True)
    revoked_by = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    last_collection_on = models.DateField(_("últim cobrament"), null=True, blank=True)

    class Meta:
        verbose_name = _("mandat SEPA")
        verbose_name_plural = _("mandats SEPA")
        constraints = [
            models.UniqueConstraint(
                fields=["member"], condition=Q(status="active"), name="sepa_mandate_one_active"
            ),
            models.CheckConstraint(
                condition=Q(reference__regex=MANDATE_REFERENCE), name="sepa_mandate_reference"
            ),
            models.CheckConstraint(
                condition=Q(status__in=MandateStatus.values), name="sepa_mandate_status_valid"
            ),
            models.CheckConstraint(
                condition=Q(sequence_type="recurrent"), name="sepa_mandate_recurrent"
            ),
            models.CheckConstraint(
                condition=(
                    Q(status="revoked") & Q(revoked_at__isnull=False) & ~Q(revoked_reason="")
                )
                # Un mandat revocat que després es bloqueja (esborrat RGPD, L-M05a-06) conserva
                # la data i el motiu de la revocació.
                | Q(status="blocked")
                | (~Q(status__in=["revoked", "blocked"]) & Q(revoked_at__isnull=True)),
                name="sepa_mandate_revoked_has_date_and_reason",
            ),
        ]

    def __str__(self):
        return self.reference


class MandateBankAccount(models.Model):
    """L'únic lloc de la plataforma amb un IBAN (044, CA-M05a-07): xifrat amb
    `apps.payments.crypto`. Cap `__str__` que el mostri i fora de l'administrador de Django."""

    mandate = models.OneToOneField(
        SepaMandate, on_delete=models.PROTECT, related_name="bank_account"
    )
    iban_ciphertext = models.BinaryField()
    key_version = models.PositiveSmallIntegerField()
    iban_country = models.CharField(max_length=2)
    iban_last4 = models.CharField(max_length=4)

    class Meta:
        verbose_name = _("compte del mandat")
        verbose_name_plural = _("comptes dels mandats")

    def __str__(self):
        return f"{self.iban_country} … {self.iban_last4}"


class FeePaymentPreference(models.Model):
    """Com vol pagar la quota el soci (RN-M05a-01). Cap fila = «sense resposta».

    La preferència i l'estat del mandat són independents: «pagar cada vegada» amb un mandat
    actiu és vàlid (P-134, opció per defecte A: el mandat es queda actiu i la remesa segueix la
    preferència). Si la resposta és la C, només canvia el flux de la pantalla, no les dades."""

    Method = FeeMethod

    member = models.OneToOneField("members.Member", on_delete=models.PROTECT, related_name="+")
    method = models.CharField(_("mètode"), max_length=14, choices=Method.choices)
    since = models.DateTimeField(_("des de"), default=timezone.now)
    set_by = models.ForeignKey("accounts.Account", on_delete=models.PROTECT, related_name="+")
    mandate = models.ForeignKey(
        SepaMandate, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    saved_card = models.ForeignKey(
        SavedCard, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )

    class Meta:
        verbose_name = _("mètode de pagament de la quota")
        verbose_name_plural = _("mètodes de pagament de la quota")
        constraints = [
            models.CheckConstraint(
                condition=Q(method__in=FeeMethod.values), name="fee_preference_method_valid"
            ),
            models.CheckConstraint(
                condition=~Q(method="direct_debit") | Q(mandate__isnull=False),
                name="fee_preference_direct_debit_has_mandate",
            ),
            models.CheckConstraint(
                condition=~Q(method="saved_card") | Q(saved_card__isnull=False),
                name="fee_preference_saved_card_has_card",
            ),
        ]

    def __str__(self):
        return self.method


class MandateCampaign(models.Model):
    """Campanya de mandats nous (escenari B, 022). Les invitacions són de la T-M05a-13."""

    name = models.CharField(_("nom"), max_length=120)
    opened_by = models.ForeignKey("accounts.Account", on_delete=models.PROTECT, related_name="+")
    opened_at = models.DateTimeField(_("oberta el"), default=timezone.now)
    closed_at = models.DateTimeField(_("tancada el"), null=True, blank=True)
    invitation_text = models.ForeignKey(
        "core.LegalText", on_delete=models.PROTECT, related_name="+"
    )

    class Meta:
        verbose_name = _("campanya de mandats")
        verbose_name_plural = _("campanyes de mandats")

    def __str__(self):
        return self.name


class MandateCampaignRecipient(models.Model):
    campaign = models.ForeignKey(
        MandateCampaign, on_delete=models.PROTECT, related_name="recipients"
    )
    member = models.ForeignKey("members.Member", on_delete=models.PROTECT, related_name="+")
    invited_at = models.DateTimeField(_("convidat el"))
    reminders_sent = models.PositiveSmallIntegerField(_("recordatoris enviats"), default=0)
    last_reminder_at = models.DateTimeField(_("últim recordatori"), null=True, blank=True)
    answered_at = models.DateTimeField(_("ha respost el"), null=True, blank=True)
    answer = models.CharField(_("resposta"), max_length=14, choices=FeeMethod.choices, blank=True)

    class Meta:
        verbose_name = _("destinatari de la campanya")
        verbose_name_plural = _("destinataris de la campanya")
        constraints = [
            models.UniqueConstraint(
                fields=["campaign", "member"], name="campaign_recipient_unique"
            ),
            models.CheckConstraint(
                condition=(Q(answer="") & Q(answered_at__isnull=True))
                | (Q(answer__in=FeeMethod.values) & Q(answered_at__isnull=False)),
                name="campaign_recipient_answer_with_date",
            ),
        ]

    def __str__(self):
        return f"{self.campaign_id}/{self.member_id}"


class DirectDebitRemittance(UndeletableModel):
    """Remesa de quotes domiciliades (M05b-6; T-M05b-09). Es crea amb
    `apps.payments.remittances.build_remittance`. Cap IBAN: el fitxer pain.008 el genera la
    T-M05b-10 a demanda, sense desar-lo."""

    class Status(models.TextChoices):
        DRAFT = "draft", _("Esborrany")
        NOTIFIED = "notified", _("Avisada")
        SENT_TO_BANK = "sent_to_bank", _("Enviada al banc")
        SETTLED = "settled", _("Liquidada")
        CANCELLED = "cancelled", _("Anul·lada")

    period = models.CharField(_("període"), max_length=20)
    collection_date = models.DateField(_("data de cobrament"))
    status = models.CharField(
        _("estat"), max_length=12, choices=Status.choices, default=Status.DRAFT
    )
    item_count = models.PositiveIntegerField(_("rebuts"))
    total_cents = models.PositiveBigIntegerField(_("import total (cèntims)"))
    # Empremta i versió de l'últim fitxer pain.008 generat; el fitxer no es desa (RN-M05b-12).
    file_hash = models.CharField(_("empremta del fitxer"), max_length=64, blank=True)
    file_format = models.CharField(_("format del fitxer"), max_length=20, blank=True)
    created_by = models.ForeignKey("accounts.Account", on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("remesa")
        verbose_name_plural = _("remeses")
        constraints = [
            models.CheckConstraint(
                condition=Q(
                    status__in=["draft", "notified", "sent_to_bank", "settled", "cancelled"]
                ),
                name="dd_remittance_status_valid",
            ),
        ]

    def __str__(self):
        return f"{self.period} ({self.collection_date})"


class DirectDebitItem(UndeletableModel):
    """Rebut domiciliat: una quota d'una remesa, amb el seu intent «enviat al banc» i el mandat
    actiu en crear la remesa (M05b-6)."""

    class Status(models.TextChoices):
        INCLUDED = "included", _("Inclòs")
        EXCLUDED = "excluded", _("Exclòs")
        COLLECTED = "collected", _("Cobrat")
        RETURNED = "returned", _("Retornat")

    remittance = models.ForeignKey(
        DirectDebitRemittance, on_delete=models.PROTECT, related_name="items"
    )
    attempt = models.OneToOneField(
        PaymentAttempt, on_delete=models.PROTECT, related_name="direct_debit_item"
    )
    mandate = models.ForeignKey(SepaMandate, on_delete=models.PROTECT, related_name="+")
    amount_cents = models.PositiveBigIntegerField(_("import (cèntims)"))
    end_to_end_id = models.CharField(
        _("identificador d'extrem a extrem"), max_length=35, unique=True
    )
    attempt_number = models.PositiveSmallIntegerField(_("intent"), default=1)
    prenotified_at = models.DateTimeField(_("avís previ enviat"), null=True, blank=True)
    status = models.CharField(
        _("estat"), max_length=10, choices=Status.choices, default=Status.INCLUDED
    )
    # Codi del banc i dia en què es registra el retorn (T-M05b-12; quins codis, P-291).
    return_reason_code = models.CharField(_("codi del retorn"), max_length=4, blank=True)
    returned_on = models.DateField(_("retornat el"), null=True, blank=True)

    class Meta:
        verbose_name = _("rebut domiciliat")
        verbose_name_plural = _("rebuts domiciliats")
        constraints = [
            models.CheckConstraint(condition=Q(amount_cents__gt=0), name="dd_item_amount_positive"),
            models.CheckConstraint(
                condition=Q(status__in=["included", "excluded", "collected", "returned"]),
                name="dd_item_status_valid",
            ),
        ]

    def __str__(self):
        return self.end_to_end_id


class RefundRequest(UndeletableModel):
    """Devolució que fa el club (M05b-6; P-M05b-G; T-M05b-13). La clau és la de la petició del
    tresorer: la mateixa clau és la mateixa devolució, de manera que un reintent després d'un
    error no la torna a fer al proveïdor ni l'apunta dues vegades a la 04 (P-118, P-119). La
    crea `apps.payments.refunds.refund`; només canvia «pendent → feta»."""

    class Channel(models.TextChoices):
        PROVIDER = "provider", _("Proveïdor")
        BANK = "bank", _("Banc")

    class Status(models.TextChoices):
        PENDING = "pending", _("Pendent")
        DONE = "done", _("Feta")

    key = models.UUIDField(_("clau"), unique=True)
    payment = models.ForeignKey(
        "core.Payment", on_delete=models.PROTECT, related_name="+", verbose_name=_("pagament")
    )
    amount_cents = models.PositiveBigIntegerField(_("import (cèntims)"))
    reason = models.TextField(_("motiu"))
    channel = models.CharField(_("canal"), max_length=8, choices=Channel.choices)
    status = models.CharField(
        _("estat"), max_length=7, choices=Status.choices, default=Status.PENDING
    )
    provider_refund_id = models.CharField(_("devolució del proveïdor"), max_length=100, blank=True)
    requested_by = models.ForeignKey("accounts.Account", on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    done_at = models.DateTimeField(_("feta el"), null=True, blank=True)

    class Meta:
        verbose_name = _("devolució")
        verbose_name_plural = _("devolucions")
        constraints = [
            models.CheckConstraint(condition=Q(amount_cents__gt=0), name="refund_amount_positive"),
            models.CheckConstraint(condition=Q(reason__regex=r"\S"), name="refund_reason_required"),
            models.CheckConstraint(
                condition=Q(channel__in=["provider", "bank"]), name="refund_channel_valid"
            ),
            models.CheckConstraint(
                condition=Q(status="pending", done_at__isnull=True)
                | Q(status="done", done_at__isnull=False),
                name="refund_done_at_iff_done",
            ),
        ]

    def __str__(self):
        return f"{self.get_status_display()} {self.amount_cents} c ({self.payment_id})"
