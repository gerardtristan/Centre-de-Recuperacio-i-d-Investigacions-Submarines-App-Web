"""Tresoreria, part mínima (M04-6). Cap altra app escriu en aquests models: ho fa amb els
serveis de la 04 (M04-8)."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    AppendOnlyModel,
    AppendOnlyQuerySet,
    Charge,
    Department,
    ImportLine,
    Payment,
    UndeletableModel,
    validate_cents,
)


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


def _active_account_ids() -> set:
    """De la base de dades: la còpia en memòria d'un compte pot ser d'abans de desactivar-lo."""
    return set(TreasuryAccount.objects.filter(active=True).values_list("pk", flat=True))


class MovementQuerySet(AppendOnlyQuerySet):
    def bulk_create(self, objs, *args, **kwargs):
        # `bulk_create` no passa per `save`: les regles del moviment nou s'apliquen igualment.
        objs = list(objs)
        active_accounts = _active_account_ids()
        for movement in objs:
            movement.validate_new(active_accounts)
        return super().bulk_create(objs, *args, **kwargs)

    def with_reversal(self):
        """Per a un llistat: porta el contramoviment de cada fila a la mateixa consulta, i
        `is_reversed` no en fa cap més."""
        return self.select_related("reversal")


class Movement(AppendOnlyModel):
    """Moviment de tresoreria (M04-6; RN-T05 a RN-T07). Només s'hi afegeixen files: el model ho
    impedeix a l'ORM i els activadors de la migració 0006 a la base de dades, també amb una
    consulta directa (CA-T06.3). Una correcció és un contramoviment (`kind = reversal`) que
    apunta l'original amb `reverses`; «anul·lat» es dedueix d'aquest enllaç i no és cap camp
    (RN-T25, CA-T17.1). El concepte no porta mai noms de persones (RNF-T4)."""

    class Direction(models.TextChoices):
        IN = "in", _("Entrada")
        OUT = "out", _("Sortida")

    class Kind(models.TextChoices):
        INCOME = "income", _("Ingrés de cobrament")
        FEE = "fee", _("Comissió")
        REFUND = "refund", _("Devolució")
        RETURN = "return", _("Retorn")
        TRANSFER = "transfer", _("Traspàs")
        CASH_ADJUSTMENT = "cash_adjustment", _("Ajust d'arqueig")
        REVERSAL = "reversal", _("Contramoviment")
        # Addenda de la 050 (RN-T26): els crea només el 09.
        EXPENSE = "expense", _("Despesa")
        OTHER_INCOME = "other_income", _("Altres ingressos")

    account = models.ForeignKey(
        TreasuryAccount,
        on_delete=models.PROTECT,
        related_name="movements",
        verbose_name=_("compte"),
    )
    direction = models.CharField(_("sentit"), max_length=3, choices=Direction.choices)
    amount_cents = models.PositiveBigIntegerField(_("import (cèntims)"))
    value_date = models.DateField(_("data de valor"))
    # RN-T31 (053): la data de valor real d'un moviment d'origen extern que ha entrat al període
    # obert perquè la seva era dins un període tancat. Buida en tots els altres.
    original_value_date = models.DateField(_("data de valor original"), null=True, blank=True)
    recorded_at = models.DateTimeField(_("data de registre"), auto_now_add=True)
    kind = models.CharField(_("tipus"), max_length=15, choices=Kind.choices)
    concept = models.CharField(_("concepte"), max_length=140)
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movements",
        verbose_name=_("departament"),
    )
    cost_centre = models.ForeignKey(
        CostCentre,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movements",
        verbose_name=_("centre de cost"),
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movements",
        verbose_name=_("pagament"),
    )
    # L'altra pota d'un traspàs. Com que cap fila no es modifica, només la segona pota apunta la
    # primera; la primera troba la segona per la relació inversa (`linked_from`). També la
    # comissió d'un retorn, que apunta el retorn (T-M04-07; així no compta com la del cobrament).
    linked_movement = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="linked_from",
        verbose_name=_("altra pota del traspàs"),
    )
    # OneToOne: un moviment només s'anul·la una vegada, i ho garanteix la base de dades.
    reverses = models.OneToOneField(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reversal",
        verbose_name=_("moviment que anul·la"),
    )
    # La liquidació del proveïdor d'on surt el moviment (els dos del traspàs del net, T-M04-13).
    settlement = models.ForeignKey(
        "ProviderSettlement",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movements",
        verbose_name=_("liquidació"),
    )
    reason = models.TextField(_("motiu"), blank=True)
    # L'identificador d'una devolució (la clau del 05b): la mateixa devolució no s'apunta dues
    # vegades (P-119, decisió 095). Únic; buit en la resta de moviments.
    refund_id = models.UUIDField(
        _("identificador de la devolució"), null=True, blank=True, unique=True
    )
    # Sense compte: l'ha creat el sistema (una notificació del proveïdor, una tasca).
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("registrat per"),
    )

    objects = MovementQuerySet.as_manager()

    class Meta:
        verbose_name = _("moviment")
        verbose_name_plural = _("moviments")
        constraints = [
            models.CheckConstraint(
                condition=Q(amount_cents__gt=0), name="movement_amount_positive"
            ),
            models.CheckConstraint(
                condition=Q(direction__in=["in", "out"]), name="movement_direction_valid"
            ),
            models.CheckConstraint(
                condition=Q(
                    kind__in=[
                        "income",
                        "fee",
                        "refund",
                        "return",
                        "transfer",
                        "cash_adjustment",
                        "reversal",
                        "expense",
                        "other_income",
                    ]
                ),
                name="movement_kind_valid",
            ),
            # RN-T05 i RN-T12: departament obligatori, tret dels traspassos, que no en porten.
            # El contramoviment porta el del moviment que anul·la (si és un traspàs, cap).
            models.CheckConstraint(
                condition=Q(kind="reversal")
                | (Q(kind="transfer") & Q(department__isnull=True))
                | (~Q(kind="transfer") & Q(department__isnull=False)),
                name="movement_department_unless_transfer",
            ),
            # RN-T09: cada pagament genera, com a màxim, un ingrés de cobrament.
            models.UniqueConstraint(
                fields=["payment"],
                condition=Q(kind="income"),
                name="movement_one_income_per_payment",
            ),
            # RN-T25: només un contramoviment apunta el moviment que anul·la.
            models.CheckConstraint(
                condition=(Q(kind="reversal") & Q(reverses__isnull=False))
                | (~Q(kind="reversal") & Q(reverses__isnull=True)),
                name="movement_reverses_only_reversal",
            ),
            models.CheckConstraint(
                condition=~Q(kind__in=["reversal", "cash_adjustment"]) | Q(reason__regex=r"\S"),
                name="movement_reason_required",
            ),
        ]
        indexes = [
            models.Index(fields=["account", "value_date"], name="movement_account_date_idx"),
            models.Index(
                fields=["department", "cost_centre", "value_date"],
                name="movement_dept_centre_date_idx",
            ),
        ]

    def __str__(self):
        sign = "+" if self.direction == self.Direction.IN else "−"
        return f"{self.get_kind_display()} {sign}{self.amount_cents} c ({self.account})"

    @property
    def is_reversed(self) -> bool:
        """«Anul·lat» (RN-T25): té un contramoviment que l'apunta. La fila no canvia mai."""
        try:
            return self.reversal is not None
        except Movement.DoesNotExist:
            return False

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.validate_new()
        super().save(*args, **kwargs)

    def validate_new(self, active_accounts=None) -> None:
        """Les regles que una restricció d'una sola fila no pot comprovar a la base de dades.
        Que el contramoviment sigui el mirall de l'original (P-M04-C) és de la T-M04-08."""
        validate_cents(self.amount_cents)
        if active_accounts is None:
            active_accounts = _active_account_ids()
        if self.account_id not in active_accounts:
            # CA-T01.3
            raise ValidationError(gettext("Un compte desactivat no admet moviments nous."))
        if self.cost_centre and self.cost_centre.department_id != self.department_id:
            raise ValidationError(
                gettext("El centre de cost ha de ser del departament del moviment.")
            )


class ProviderSettlement(UndeletableModel):
    """Liquidació d'un proveïdor de cobrament (M04-6; RN-T21; T-M04-13): l'abonament agrupat,
    amb el brut, les comissions, el net i una partida per cobrament (`SettlementItem`). Només
    canvia l'estat: rebuda → conciliada; «a revisar» quan una línia no és d'un cobrament conegut
    (CA-T11.2), amb els problemes a `review_notes`. El format real és [A verificar: P-45]."""

    class Status(models.TextChoices):
        RECEIVED = "received", _("Rebuda")
        RECONCILED = "reconciled", _("Conciliada")
        TO_REVIEW = "to_review", _("A revisar")

    class Source(models.TextChoices):
        NOTIFICATION = "notification", _("Notificació")
        FILE = "file", _("Fitxer")
        MANUAL = "manual", _("Manual")
        REMITTANCE = "remittance", _("Remesa")

    provider_code = models.CharField(_("proveïdor"), max_length=30)
    external_id = models.CharField(_("identificador del proveïdor"), max_length=100)
    settled_on = models.DateField(_("data de l'abonament"))
    gross_cents = models.PositiveBigIntegerField(_("brut (cèntims)"))
    fees_cents = models.PositiveBigIntegerField(_("comissions (cèntims)"))
    net_cents = models.PositiveBigIntegerField(_("net (cèntims)"))
    status = models.CharField(_("estat"), max_length=10, choices=Status.choices)
    source = models.CharField(_("origen"), max_length=12, choices=Source.choices)
    review_notes = models.JSONField(_("problemes"), default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("liquidació")
        verbose_name_plural = _("liquidacions")
        constraints = [
            models.UniqueConstraint(
                fields=["provider_code", "external_id"], name="settlement_unique_per_provider"
            ),
            models.CheckConstraint(
                condition=Q(net_cents=F("gross_cents") - F("fees_cents")),
                name="settlement_net_is_gross_minus_fees",
            ),
            models.CheckConstraint(
                condition=Q(gross_cents__gt=0) & Q(net_cents__gt=0),
                name="settlement_amounts_positive",
            ),
            models.CheckConstraint(
                condition=Q(status__in=["received", "reconciled", "to_review"]),
                name="settlement_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(source__in=["notification", "file", "manual", "remittance"]),
                name="settlement_source_valid",
            ),
        ]

    def __str__(self):
        return f"{self.provider_code} {self.external_id}"


class SettlementItem(AppendOnlyModel):
    """Una partida de la liquidació: un cobrament (un pagament només és en una liquidació),
    l'import i, si el proveïdor la detalla, la comissió (M04-6; S-M04-05)."""

    settlement = models.ForeignKey(
        ProviderSettlement,
        on_delete=models.PROTECT,
        related_name="items",
        verbose_name=_("liquidació"),
    )
    payment = models.OneToOneField(
        Payment, on_delete=models.PROTECT, related_name="+", verbose_name=_("pagament")
    )
    amount_cents = models.PositiveBigIntegerField(_("import (cèntims)"))
    fee_cents = models.PositiveBigIntegerField(_("comissió (cèntims)"), null=True, blank=True)

    class Meta:
        verbose_name = _("partida de liquidació")
        verbose_name_plural = _("partides de liquidació")
        constraints = [
            models.CheckConstraint(
                condition=Q(amount_cents__gt=0), name="settlement_item_amount_positive"
            ),
        ]


class TransferReference(AppendOnlyModel):
    """Referència de transferència d'un càrrec (M04-6; RN-T20): una per càrrec, única i que no
    canvia mai. La crea `treasury.transfer_reference` (`references.py`)."""

    charge = models.OneToOneField(
        Charge, on_delete=models.PROTECT, related_name="+", verbose_name=_("càrrec")
    )
    reference = models.CharField(_("referència"), max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("referència de transferència")
        verbose_name_plural = _("referències de transferència")

    def __str__(self):
        return self.reference


class StatementLineState(UndeletableModel):
    """Estat d'una línia de l'extracte a la conciliació (M04-6; RN-T14, RN-T15): pendent →
    proposada → conciliada; pendent → exclosa. «A revisar» és una marca amb el seu motiu. La
    línia de la 00 no es toca mai. El manté `reconciliation.refresh` (T-M04-11)."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Pendent")
        PROPOSED = "proposed", _("Proposada")
        RECONCILED = "reconciled", _("Conciliada")
        EXCLUDED = "excluded", _("Exclosa")

    class ReviewReason(models.TextChoices):
        AMOUNT_MISMATCH = "amount_mismatch", _("L'import no coincideix amb el dels càrrecs")
        CHARGE_NOT_PENDING = "charge_not_pending", _("El càrrec ja no està pendent")
        UNKNOWN_REFERENCE = "unknown_reference", _("La referència no és de cap càrrec")
        REPEATED_REFERENCE = "repeated_reference", _("El càrrec ja és en una altra proposta")
        AMOUNT_ONLY = "amount_only", _("Sense referència: un sol càrrec pendent amb aquest import")
        SETTLEMENT_AMBIGUOUS = (
            "settlement_ambiguous",
            _("Més d'una liquidació o línia amb aquest import: cal triar-la"),
        )

    # L'estat no és cap conciliació: no bloqueja desfer l'extracte (V-06; només ho fa una
    # `Reconciliation` vigent, `reconciliation.has_live_reconciliations`).
    statement_line = models.OneToOneField(
        ImportLine, on_delete=models.PROTECT, related_name="+", verbose_name=_("línia")
    )
    status = models.CharField(
        _("estat"), max_length=10, choices=Status.choices, default=Status.PENDING
    )
    to_review = models.BooleanField(_("a revisar"), default=False)
    review_reason = models.CharField(
        _("motiu de la revisió"), max_length=20, choices=ReviewReason.choices, blank=True
    )
    # El motiu que escriu el tresorer en excloure-la (RN-T15, CA-T12.1; T-M04-14).
    exclusion_reason = models.TextField(_("motiu de l'exclusió"), blank=True)
    # La proposta que el tresorer confirmarà (T-M04-12): un càrrec, o diversos si la línia en
    # porta les referències i la suma és exacta (LT5).
    proposed_charges = models.ManyToManyField(
        Charge, blank=True, related_name="+", verbose_name=_("càrrecs proposats")
    )
    # O la liquidació del proveïdor pel net (T-M04-13b; P-M04-F pas 2), mai totes dues coses.
    proposed_settlement = models.ForeignKey(
        "ProviderSettlement",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("liquidació proposada"),
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("estat de línia de l'extracte")
        verbose_name_plural = _("estats de línies de l'extracte")
        constraints = [
            models.CheckConstraint(
                condition=Q(to_review=False, review_reason="")
                | (Q(to_review=True) & ~Q(review_reason="")),
                name="statement_line_review_reason_iff_flag",
            ),
            models.CheckConstraint(
                condition=Q(status="excluded", to_review=False) & ~Q(exclusion_reason="")
                | (~Q(status="excluded") & Q(exclusion_reason="")),
                name="statement_line_excluded_iff_reason",
            ),
        ]

    def __str__(self):
        return f"{self.get_status_display()} ({self.statement_line_id})"


class Reconciliation(AppendOnlyModel):
    """Conciliació confirmada pel tresorer (M04-6; RN-T16, RN-T17): una línia de l'extracte
    casada amb un o més càrrecs. Només INSERT, també a la base de dades (migració 0010). La crea
    `reconciliation.confirm` (T-M04-12); desfer-la és una fila nova (`ReconciliationUndo`, 045).
    `settlement`: la liquidació casada pel net (T-M04-13b; `settlements.confirm`)."""

    # Una conciliació vigent (sense desfeta) bloqueja desfer l'extracte (V-06): la 04 ho respon
    # al senyal `bank_statement.reconciled_lines` (`reconciliation.has_live_reconciliations`).
    statement_line = models.ForeignKey(
        ImportLine,
        on_delete=models.PROTECT,
        related_name="reconciliations",
        verbose_name=_("línia"),
    )
    matched_charges = models.ManyToManyField(
        Charge, related_name="+", verbose_name=_("càrrecs casats")
    )
    settlement = models.ForeignKey(
        "ProviderSettlement",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reconciliations",
        verbose_name=_("liquidació"),
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("confirmada per"),
    )
    confirmed_at = models.DateTimeField(_("data de la confirmació"), auto_now_add=True)

    class Meta:
        verbose_name = _("conciliació")
        verbose_name_plural = _("conciliacions")

    def __str__(self):
        return f"{self._meta.verbose_name} {self.pk} ({self.statement_line_id})"


class ReconciliationUndo(AppendOnlyModel):
    """Desfeta d'una conciliació (M04-6; RN-T19; 045; CA-T10.4 a CA-T10.6): una per conciliació,
    amb el motiu, qui i quan. Una conciliació és vigent si no en té. Només INSERT, també a la base
    de dades (migració 0012). La crea `reconciliation.undo`."""

    reconciliation = models.OneToOneField(
        Reconciliation, on_delete=models.PROTECT, related_name="undo", verbose_name=_("conciliació")
    )
    reason = models.TextField(_("motiu"))
    undone_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("desfeta per"),
    )
    undone_at = models.DateTimeField(_("data de la desfeta"), auto_now_add=True)

    class Meta:
        verbose_name = _("desfeta de conciliació")
        verbose_name_plural = _("desfetes de conciliació")
        constraints = [
            models.CheckConstraint(
                condition=Q(reason__regex=r"\S"), name="reconciliation_undo_reason_required"
            ),
        ]

    def __str__(self):
        return f"{self._meta.verbose_name} {self.reconciliation_id}"


class CashCount(AppendOnlyModel):
    """Arqueig d'un compte de caixa (M04-6; HU-T08; P-M04-D; CA-T08.1): l'import comptat, el
    saldo calculat a la mateixa data i la diferència. No crea cap moviment sol; si el tresorer ho
    demana, porta l'ajust (VT-06) que ha creat la mateixa crida. Només INSERT, també a la base de
    dades (migració 0014). El crea `services.record_cash_count`."""

    account = models.ForeignKey(
        TreasuryAccount,
        on_delete=models.PROTECT,
        related_name="cash_counts",
        verbose_name=_("compte"),
    )
    counted_on = models.DateField(_("data de l'arqueig"))
    counted_cents = models.PositiveBigIntegerField(_("import comptat (cèntims)"))
    computed_cents = models.BigIntegerField(_("saldo calculat (cèntims)"))
    difference_cents = models.BigIntegerField(_("diferència (cèntims)"))
    adjustment = models.OneToOneField(
        Movement,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="cash_count",
        verbose_name=_("ajust"),
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("registrat per"),
    )
    recorded_at = models.DateTimeField(_("data de registre"), auto_now_add=True)

    class Meta:
        verbose_name = _("arqueig")
        verbose_name_plural = _("arqueigs")
        constraints = [
            models.CheckConstraint(
                condition=Q(difference_cents=F("counted_cents") - F("computed_cents")),
                name="cash_count_difference_is_counted_minus_computed",
            ),
            models.CheckConstraint(
                condition=Q(adjustment__isnull=True) | ~Q(difference_cents=0),
                name="cash_count_adjustment_only_with_difference",
            ),
        ]

    def __str__(self):
        return f"{self._meta.verbose_name} {self.account} {self.counted_on}"
