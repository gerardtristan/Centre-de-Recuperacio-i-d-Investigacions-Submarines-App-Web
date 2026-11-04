"""Models del M01 (T-M01-11; planning.md, M01-6 i addendes de la 058 i la 064).

Només l'estructura i les restriccions que garanteix la base de dades. Les transicions, el
número de soci, les quotes, els carnets i les llicències els porten els serveis de les tasques
següents: cap altra app escriu en aquests models si no és a través d'aquests serveis.

Cap camp de salut, d'IBAN ni de data de naixement. Totes les relacions són PROTECT: les
persones s'anonimitzen i els comptes es desactiven, però no s'esborren (028, RN-25); el soci
i el seu número no s'esborren mai (039); l'historial, les quotes i les llicències tampoc.
Els camps `import_batch` els afegeix la T-M01-24 amb el lot d'importació.
"""

from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Length, Trim
from django.db.models.lookups import GreaterThan
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import AppendOnlyModel, Charge, Person, UndeletableModel


def _filled(field):
    # Text amb alguna cosa més que espais (TRIM de PostgreSQL treu els espais ordinaris).
    return Q(GreaterThan(Length(Trim(field)), 0))


class MembershipType(models.Model):
    """Tipus de soci. Un tipus amb socis no s'esborra: es desactiva."""

    code = models.CharField(_("codi"), max_length=20, unique=True)
    name = models.CharField(_("nom"), max_length=60)
    annual_fee_cents = models.PositiveIntegerField(_("quota anual (cèntims)"))
    active = models.BooleanField(_("actiu"), default=True)

    class Meta:
        verbose_name = _("tipus de soci")
        verbose_name_plural = _("tipus de soci")
        constraints = [
            models.CheckConstraint(
                condition=Q(annual_fee_cents__gt=0), name="membershiptype_fee_positive"
            ),
        ]

    def __str__(self):
        return self.name


class Member(models.Model):
    """Soci: relació d'una persona amb el club. Una readmissió fa servir el mateix registre."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Pendent")
        ACTIVE = "active", _("Actiu")
        UNPAID = "unpaid", _("Impagat")
        LEFT = "left", _("Baixa")

    person = models.OneToOneField(
        Person, on_delete=models.PROTECT, related_name="member", verbose_name=_("persona")
    )
    member_number = models.PositiveIntegerField(_("número de soci"), null=True, blank=True)
    type = models.ForeignKey(
        MembershipType, on_delete=models.PROTECT, related_name="members", verbose_name=_("tipus")
    )
    # Només canvia amb els serveis d'estat (RN-M01-08, T-M01-12).
    status = models.CharField(
        _("estat"), max_length=10, choices=Status.choices, default=Status.PENDING
    )
    joined_on = models.DateField(_("data d'alta"))
    joined_on_is_approximate = models.BooleanField(_("data d'alta aproximada"), default=False)
    left_on = models.DateField(_("data de baixa"), null=True, blank=True)
    # Null (M01-6) i no "": l'únic parcial només s'aplica als socis que vénen de Cluber.
    cluber_id = models.CharField(  # noqa: DJ001
        _("identificador de Cluber"), max_length=40, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("soci")
        verbose_name_plural = _("socis")
        constraints = [
            # El número no es repeteix mai en tota la història (039).
            models.UniqueConstraint(
                fields=["member_number"],
                condition=Q(member_number__isnull=False),
                name="member_unique_number",
            ),
            models.UniqueConstraint(
                fields=["cluber_id"],
                condition=Q(cluber_id__isnull=False),
                name="member_unique_cluber_id",
            ),
            models.CheckConstraint(
                condition=Q(status__in=["pending", "active", "unpaid", "left"]),
                name="member_status_valid",
            ),
            # Destí de la clau forana composta de `MemberRequest` (migració 0001).
            models.UniqueConstraint(fields=["id", "person"], name="member_id_person"),
        ]
        indexes = [models.Index(fields=["status", "type"], name="member_status_type_idx")]

    def __str__(self):
        return f"{self.member_number or '—'} {self.person}"


class MemberStatusChange(AppendOnlyModel):
    """Historial d'estats i tipus (RN-M01-08). Només s'hi afegeixen files: també ho
    imposen uns disparadors de PostgreSQL (migració 0003). L'excepció acotada per anonimitzar
    `reason` en un esborrat RGPD és de la T-M01-22."""

    member = models.ForeignKey(
        Member, on_delete=models.PROTECT, related_name="status_changes", verbose_name=_("soci")
    )
    from_status = models.CharField(
        _("estat anterior"), max_length=10, choices=Member.Status.choices, blank=True
    )
    to_status = models.CharField(_("estat nou"), max_length=10, choices=Member.Status.choices)
    from_type = models.ForeignKey(
        MembershipType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("tipus anterior"),
    )
    to_type = models.ForeignKey(
        MembershipType, on_delete=models.PROTECT, related_name="+", verbose_name=_("tipus nou")
    )
    effective_on = models.DateField(_("data efectiva"))
    reason = models.TextField(_("motiu"), blank=True)
    # Null quan l'acció és del sistema.
    actor_account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("compte"),
    )
    created_at = models.DateTimeField(_("data i hora"), default=timezone.now)

    class Meta:
        verbose_name = _("canvi d'estat o de tipus")
        verbose_name_plural = _("historial dels socis")
        constraints = [
            models.CheckConstraint(
                condition=Q(from_status__in=["", "pending", "active", "unpaid", "left"]),
                name="memberstatuschange_from_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(to_status__in=["pending", "active", "unpaid", "left"]),
                name="memberstatuschange_to_status_valid",
            ),
            # Motiu obligatori en baixa, impagat i desmarcar l'impagat (M01-6).
            models.CheckConstraint(
                condition=~(
                    Q(to_status__in=["left", "unpaid"])
                    | Q(from_status="unpaid", to_status="active")
                )
                | _filled("reason"),
                name="memberstatuschange_reason_when_required",
            ),
        ]
        indexes = [
            models.Index(fields=["member", "created_at"], name="memberstatuschange_member_idx")
        ]

    def __str__(self):
        return f"{self.member_id}: {self.from_status or '—'} → {self.to_status}"


class MemberRequest(models.Model):
    """Sol·licitud d'alta, de canvi de tipus o de baixa. El motiu de qui la fa i el de qui la
    resol són camps separats (064, CA-M01-47)."""

    class Kind(models.TextChoices):
        JOIN = "join", _("Alta")
        CHANGE_TYPE = "change_type", _("Canvi de tipus")
        LEAVE = "leave", _("Baixa")

    class Channel(models.TextChoices):
        WEB = "web", _("Web")
        IN_PERSON = "in_person", _("Presencial")

    class Status(models.TextChoices):
        PENDING = "pending", _("Pendent")
        APPROVED = "approved", _("Aprovada")
        REJECTED = "rejected", _("Rebutjada")
        CANCELLED = "cancelled", _("Cancel·lada")

    kind = models.CharField(_("tipus de sol·licitud"), max_length=12, choices=Kind.choices)
    # Per a una alta, la persona creada o trobada. Si hi ha soci, és la seva persona (clau
    # forana composta de la migració 0001).
    person = models.ForeignKey(
        Person, on_delete=models.PROTECT, related_name="member_requests", verbose_name=_("persona")
    )
    member = models.ForeignKey(
        Member,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="requests",
        verbose_name=_("soci"),
    )
    requested_type = models.ForeignKey(
        MembershipType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("tipus demanat"),
    )
    request_reason = models.TextField(_("motiu de la sol·licitud"), blank=True)
    resolution_reason = models.TextField(_("motiu de la resolució"), blank=True)
    channel = models.CharField(_("canal"), max_length=10, choices=Channel.choices)
    status = models.CharField(
        _("estat"), max_length=10, choices=Status.choices, default=Status.PENDING
    )
    # La coherència entre l'estat i qui i quan la resol no la fixa el pla: és dels serveis
    # que la resolen (T-M01-14, T-M01-17).
    resolved_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("resolta per"),
    )
    resolved_at = models.DateTimeField(_("resolta el"), null=True, blank=True)
    effective_on = models.DateField(_("data efectiva"), null=True, blank=True)
    # Coincidències trobades (V-03), sense dades sensibles.
    duplicate_warning = models.JSONField(_("avís de possible duplicat"), default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("sol·licitud de soci")
        verbose_name_plural = _("sol·licituds de soci")
        constraints = [
            models.CheckConstraint(
                condition=Q(kind__in=["join", "change_type", "leave"]),
                name="memberrequest_kind_valid",
            ),
            models.CheckConstraint(
                condition=Q(channel__in=["web", "in_person"]), name="memberrequest_channel_valid"
            ),
            models.CheckConstraint(
                condition=Q(status__in=["pending", "approved", "rejected", "cancelled"]),
                name="memberrequest_status_valid",
            ),
            models.CheckConstraint(
                condition=~Q(kind="leave") | _filled("request_reason"),
                name="memberrequest_leave_has_reason",
            ),
            models.CheckConstraint(
                condition=~Q(status="rejected") | _filled("resolution_reason"),
                name="memberrequest_rejection_has_reason",
            ),
            models.CheckConstraint(
                condition=Q(kind__in=["join", "change_type"], requested_type__isnull=False)
                | Q(kind="leave", requested_type__isnull=True),
                name="memberrequest_requested_type_by_kind",
            ),
            models.CheckConstraint(
                condition=Q(kind="join") | Q(member__isnull=False),
                name="memberrequest_member_by_kind",
            ),
            models.UniqueConstraint(
                fields=["person", "kind"],
                condition=Q(status="pending"),
                name="memberrequest_one_pending_per_kind",
            ),
        ]

    def __str__(self):
        return f"{self.get_kind_display()} {self.person_id} ({self.get_status_display()})"


class MembershipNumberCounter(models.Model):
    """Últim número de soci assignat, en una sola fila. No és una seqüència de PostgreSQL,
    que consumiria números en desfer una transacció. Que no es reiniciï ni es reutilitzi cap
    número ho garanteix el servei que l'assigna amb `SELECT … FOR UPDATE` (T-M01-14) i
    l'únic de `Member.member_number`."""

    last_number = models.PositiveIntegerField(_("últim número"), default=0)

    class Meta:
        verbose_name = _("comptador de números de soci")
        verbose_name_plural = _("comptador de números de soci")
        constraints = [models.CheckConstraint(condition=Q(id=1), name="counter_single_row")]

    def __str__(self):
        return str(self.last_number)


class AnnualFee(UndeletableModel):
    """Quota d'un soci sobre un càrrec de la 00 (RN-M01-51: no s'esborra). L'import i l'estat
    són els del càrrec. La generació i el venciment (P-29) són de la T-M01-14 i la T-M01-18."""

    class Kind(models.TextChoices):
        ANNUAL = "annual", _("Quota anual")
        TYPE_CHANGE_SUPPLEMENT = "type_change_supplement", _("Suplement de canvi de tipus")

    member = models.ForeignKey(
        Member, on_delete=models.PROTECT, related_name="fees", verbose_name=_("soci")
    )
    period = models.PositiveSmallIntegerField(_("període"))
    kind = models.CharField(_("tipus de quota"), max_length=25, choices=Kind.choices)
    charge = models.OneToOneField(
        Charge, on_delete=models.PROTECT, related_name="annual_fee", verbose_name=_("càrrec")
    )
    due_on = models.DateField(_("venciment"))

    class Meta:
        verbose_name = _("quota")
        verbose_name_plural = _("quotes")
        constraints = [
            models.UniqueConstraint(
                fields=["member", "period", "kind"], name="annualfee_unique_period_kind"
            ),
            models.CheckConstraint(
                condition=Q(kind__in=["annual", "type_change_supplement"]),
                name="annualfee_kind_valid",
            ),
        ]

    def __str__(self):
        return f"{self.member_id} {self.period} {self.kind}"


class MemberCard(models.Model):
    """Carnet. Només es desa l'empremta del testimoni. El format de `token_hash` és el d'un
    SHA-256 en hexadecimal, però això no impedeix desar-hi un testimoni en clar que tingui
    aquest format: generar el testimoni i resumir-lo és del servei del carnet (T-M01-19)."""

    member = models.ForeignKey(
        Member, on_delete=models.PROTECT, related_name="cards", verbose_name=_("soci")
    )
    token_hash = models.CharField(_("empremta del testimoni"), max_length=64, unique=True)
    issued_at = models.DateTimeField(_("emès el"), default=timezone.now)
    revoked_at = models.DateTimeField(_("revocat el"), null=True, blank=True)
    revoked_reason = models.TextField(_("motiu de la revocació"), blank=True)

    class Meta:
        verbose_name = _("carnet")
        verbose_name_plural = _("carnets")
        constraints = [
            models.CheckConstraint(
                # Format de l'empremta, no cap contrasenya.
                condition=Q(token_hash__regex=r"^[0-9a-f]{64}$"),  # noqa: S106
                name="membercard_token_hash_sha256_hex",
            ),
            models.UniqueConstraint(
                fields=["member"],
                condition=Q(revoked_at__isnull=True),
                name="membercard_one_active_per_member",
            ),
            models.CheckConstraint(
                condition=Q(revoked_at__isnull=True, revoked_reason="")
                | (Q(revoked_at__isnull=False) & _filled("revoked_reason")),
                name="membercard_revoked_with_reason",
            ),
        ]

    def __str__(self):
        return f"{self.member_id} {self.issued_at:%Y-%m-%d}"


class LicenceRecord(models.Model):
    """Registre mínim de llicència (RN-M01-29). `expires_on` pot ser buit: caducitat
    desconeguda (addenda de la 058). `licence_type` és text lliure fins a la 06."""

    class Source(models.TextChoices):
        MANUAL = "manual", _("Manual")
        CLUBER = "cluber", _("Cluber")

    member = models.ForeignKey(
        Member, on_delete=models.PROTECT, related_name="licence_records", verbose_name=_("soci")
    )
    licence_type = models.CharField(_("tipus de llicència"), max_length=100)
    issued_on = models.DateField(_("data d'alta"))
    expires_on = models.DateField(_("data de caducitat"), null=True, blank=True)
    source = models.CharField(_("origen"), max_length=10, choices=Source.choices)

    class Meta:
        verbose_name = _("registre de llicència")
        verbose_name_plural = _("registres de llicència")
        constraints = [
            models.CheckConstraint(
                condition=Q(expires_on__isnull=True) | Q(expires_on__gte=F("issued_on")),
                name="licencerecord_expires_after_issue",
            ),
            models.CheckConstraint(
                condition=Q(source__in=["manual", "cluber"]), name="licencerecord_source_valid"
            ),
        ]

    def __str__(self):
        return f"{self.member_id} {self.licence_type}"
