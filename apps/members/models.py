"""Models del M01 (T-M01-11; planning.md, M01-6 i addendes de la 058 i la 064).

Només l'estructura i les restriccions que garanteix la base de dades. Les transicions, el
número de soci, les quotes, els carnets i les llicències els porten els serveis de les tasques
següents: cap altra app escriu en aquests models si no és a través d'aquests serveis.

Cap camp de salut ni d'IBAN. L'única data de naixement és la que porta una sol·licitud d'alta
(068; `Person.birth_date` és de la T-M01-33), amb la mateixa visibilitat (C1). Totes les
relacions són PROTECT: les persones s'anonimitzen i els comptes es desactiven, però no
s'esborren (028, RN-25); el soci i el seu número no s'esborren mai (039); l'historial, les
quotes i les llicències tampoc.
Els camps `import_batch` els afegeix la T-M01-24 amb el lot d'importació.
"""

import secrets

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Length, Trim
from django.db.models.lookups import GreaterThan
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    AppendOnlyModel,
    Charge,
    Person,
    UndeletableModel,
    UndeletableQuerySet,
)


def _filled(field):
    # Text amb alguna cosa més que espais (TRIM de PostgreSQL treu els espais ordinaris).
    return Q(GreaterThan(Length(Trim(field)), 0))


def new_avatar_seed():
    # Font aleatòria segura del sistema, mai cap dada personal (RN-M01-30, lectura de la 060).
    return secrets.token_hex(32)


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
    # Buida només en un soci importat de Cluber sense data d'alta (072, Q-075): no se n'inventa
    # cap i no es mostra l'antiguitat; la secretaria la pot posar després (RN-M01-22).
    joined_on = models.DateField(_("data d'alta"), null=True, blank=True)
    joined_on_is_approximate = models.BooleanField(_("data d'alta aproximada"), default=False)
    left_on = models.DateField(_("data de baixa"), null=True, blank=True)
    # Null (M01-6) i no "": l'únic parcial només s'aplica als socis que vénen de Cluber.
    cluber_id = models.CharField(  # noqa: DJ001
        _("identificador de Cluber"), max_length=40, null=True, blank=True
    )
    # «Data alta/renovació» de l'exportació de Cluber (072, Q-076): el carnet d'un soci importat
    # val un any des d'aquesta data, fins al mateix dia de l'any següent [A validar: tresorer].
    # Només per a socis de Cluber (restricció). La desa la importació final (T-M01-25).
    cluber_renewed_on = models.DateField(_("última renovació a Cluber"), null=True, blank=True)
    # Fixada en l'alta per a l'avatar futur; un disparador impedeix canviar-la (members/0004).
    # Només la genera `new_avatar_seed`, des del servei d'alta (T-M01-14). El format de 64
    # caràcters hexadecimals (members/0005) no demostra que sigui aleatòria.
    avatar_seed = models.CharField(
        _("llavor de l'avatar"), max_length=64, default=new_avatar_seed, editable=False
    )
    # Només als socis creats per un lot (T-M01-24); PROTECT protegeix el lot, no el soci.
    import_batch = models.ForeignKey(
        "core.ImportBatch",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("lot d'importació"),
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
            models.CheckConstraint(
                condition=Q(joined_on__isnull=False) | Q(import_batch__isnull=False),
                name="member_joined_on_only_imported_may_be_empty",
            ),
            models.CheckConstraint(
                condition=Q(cluber_renewed_on__isnull=True) | Q(cluber_id__isnull=False),
                name="member_cluber_renewed_only_cluber",
            ),
            # Destí de la clau forana composta de `MemberRequest` (migració 0001).
            models.UniqueConstraint(fields=["id", "person"], name="member_id_person"),
            models.CheckConstraint(
                condition=Q(avatar_seed__regex=r"^[0-9a-f]{64}$"),
                name="member_avatar_seed_hex64",
            ),
        ]
        indexes = [models.Index(fields=["status", "type"], name="member_status_type_idx")]

    def __str__(self):
        return f"{self.member_number or '—'} {self.person}"


class MemberStatusChange(AppendOnlyModel):
    """Historial d'estats i tipus (RN-M01-08). Només s'hi afegeixen files: també ho
    imposen uns disparadors de PostgreSQL (migració 0003). Única excepció, acotada al disparador
    (migració 0018, T-M01-22): en un esborrat RGPD, `reason` passa a ser la referència."""

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

    class Origin(models.TextChoices):
        PLATFORM = "platform", _("plataforma")
        CLUBER_IMPORT = "cluber_import", _("importat de Cluber")

    # Procedència de l'entrada (072, Q-072): distingeix l'entrada inicial d'un soci importat d'un
    # canvi fet a la plataforma. Sense data d'alta, la data efectiva és la de la importació.
    origin = models.CharField(
        _("procedència"), max_length=20, choices=Origin.choices, default=Origin.PLATFORM
    )
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
            models.CheckConstraint(
                condition=Q(origin__in=["platform", "cluber_import"]),
                name="memberstatuschange_origin_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["member", "created_at"], name="memberstatuschange_member_idx")
        ]

    def __str__(self):
        return f"{self.member_id}: {self.from_status or '—'} → {self.to_status}"


class MemberJoinDateChange(AppendOnlyModel):
    """Correccions de la data d'alta (RN-M01-22, T-M01-15b): el valor anterior i el nou, amb la
    marca d'aproximada. Les fa sempre un compte amb P6, mai el sistema. Només s'hi afegeixen
    files: també ho imposen uns disparadors de PostgreSQL (migració 0009). Sense text lliure."""

    member = models.ForeignKey(
        Member, on_delete=models.PROTECT, related_name="join_date_changes", verbose_name=_("soci")
    )
    # Buida quan el soci importat no en tenia cap (072, Q-075).
    from_joined_on = models.DateField(_("data d'alta anterior"), null=True, blank=True)
    from_is_approximate = models.BooleanField(_("aproximada abans"))
    to_joined_on = models.DateField(_("data d'alta nova"))
    to_is_approximate = models.BooleanField(_("aproximada ara"))
    actor_account = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, related_name="+", verbose_name=_("compte")
    )
    created_at = models.DateTimeField(_("data i hora"), default=timezone.now)

    class Meta:
        verbose_name = _("correcció de la data d'alta")
        verbose_name_plural = _("correccions de la data d'alta")
        constraints = [
            models.CheckConstraint(
                condition=~Q(
                    from_joined_on=F("to_joined_on"), from_is_approximate=F("to_is_approximate")
                ),
                name="memberjoindatechange_changes_something",
            ),
        ]
        indexes = [models.Index(fields=["member", "created_at"], name="joindatechange_member_idx")]


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
    # Alta (068, RN-M01-62): la data declarada a la sol·licitud, amb la visibilitat de C1. Buida
    # només a les sol·licituds anteriors a la migració 0007: per a les noves l'exigeixen el
    # formulari i `join.submit`; aprovar-ne una sense data es rebutja (T-M01-35, CA-M01-41).
    birth_date = models.DateField(_("data de naixement"), null=True, blank=True)
    # Pare, mare o tutor legal d'un menor (RN-M01-62): tot o res. Visibilitat del document: C2.
    # Cap vista no els edita; només els canviarà l'anonimització (T-M01-22).
    # Q-042 (072): el correu i el telèfon escrits a la sol·licitud quan el document ja era d'una
    # persona existent i no coincideixen amb els seus. Només els veu qui revisa l'alta (P3); la
    # secretaria decideix en aprovar si actualitza la persona, amb registre. S'anonimitzen amb la
    # resta de la sol·licitud (T-M01-22).
    new_contact_email = models.EmailField(_("correu nou de contacte"), blank=True, default="")
    new_contact_phone = models.CharField(
        _("telèfon nou de contacte"), max_length=30, blank=True, default=""
    )
    # T-M01-17 (072): el suplement d'un canvi de tipus aprovat; en pagar-lo, el canvi es fa.
    supplement_fee = models.OneToOneField(
        "AnnualFee",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="type_change_request",
        verbose_name=_("suplement"),
    )
    # T-M01-17 (074, RN-M01-74): quan s'ha aplicat una baixa validada. Buida en una baixa
    # aprovada vol dir programada (data efectiva futura): l'aplica la tasca diària una sola vegada.
    applied_at = models.DateTimeField(_("baixa aplicada el"), null=True, blank=True)
    guardian_first_name = models.CharField(_("nom del representant"), max_length=100, blank=True)
    guardian_last_name = models.CharField(_("cognoms del representant"), max_length=150, blank=True)
    guardian_id_document_type = models.CharField(
        _("tipus de document del representant"),
        max_length=10,
        choices=Person.DocumentType.choices,
        blank=True,
    )
    guardian_id_document_number = models.CharField(
        _("document del representant"), max_length=30, blank=True
    )
    # T-M01-41 (072, Q-011 opció 3): on van les comunicacions d'un menor (RN-M01-78,
    # `recipients.email_for`). Normalitzats com els de la persona; els exigeix el servei per a les
    # sol·licituds noves (les anteriors a la migració 0017 no en tenen).
    guardian_email = models.EmailField(_("correu del representant"), blank=True, default="")
    guardian_phone = models.CharField(
        _("telèfon del representant"), max_length=30, blank=True, default=""
    )
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
            # Representant: tot o res (068). Les dades d'un menor sense representant les rebutja
            # el servei, perquè l'edat depèn del dia de la sol·licitud. T-M01-41: el correu i el
            # telèfon, junts i només amb un representant; poden faltar tots dos només a les
            # sol·licituds anteriors (el servei els exigeix a les noves). Passaport: Q-017.
            models.CheckConstraint(
                condition=Q(
                    guardian_first_name="",
                    guardian_last_name="",
                    guardian_id_document_type="",
                    guardian_id_document_number="",
                    guardian_email="",
                    guardian_phone="",
                )
                | (
                    _filled("guardian_first_name")
                    & _filled("guardian_last_name")
                    & Q(guardian_id_document_type__in=["dni", "nie", "passport"])
                    & _filled("guardian_id_document_number")
                    & (
                        Q(guardian_email="", guardian_phone="")
                        | (_filled("guardian_email") & _filled("guardian_phone"))
                    )
                ),
                name="memberrequest_guardian_all_or_nothing",
            ),
            models.CheckConstraint(
                condition=Q(kind="join")
                | Q(birth_date__isnull=True, guardian_id_document_number=""),
                name="memberrequest_birth_and_guardian_only_for_join",
            ),
        ]

    def __str__(self):
        return f"{self.get_kind_display()} {self.person_id} ({self.get_status_display()})"


class JoinAcceptance(AppendOnlyModel):
    """Acceptació d'un text legal en una sol·licitud d'alta (068, RN-M01-63; regla uniforme del
    06/11/2026). En enviar l'alta no es crea cap `core.Consent`: l'acceptació queda aquí, lligada
    a la sol·licitud, amb el text i la versió, qui l'accepta, per a qui, el canal i, a l'alta
    presencial, el compte que la registra. Què se'n fa en aprovar l'alta és de la T-M01-14.

    - **Qui:** «sol·licitant» (qui demana l'alta per a si mateix, adult) o «representant» (el
      pare, la mare o el tutor legal amb les dades de la mateixa sol·licitud). Mai no es desa com
      a acceptació del menor el que ha acceptat el representant. Excepció (T-M01-41, RN-M01-78):
      el butlletí i les imatges d'un menor de 14 a 17 anys els accepta el mateix menor
      («sol·licitant») [A validar: assessor de protecció de dades, Q-016].
    - **Per a qui:** el sol·licitant de la sol·licitud. A propòsit, no hi ha cap clau cap a
      `Person`: si el document coincidia amb una persona existent, l'acceptació no se li atribueix
      (RN-M01-66); la T-M01-14 decideix què se'n fa quan l'administració hagi comprovat la
      identitat.
    - **Immutable** (model i disparadors de la migració 0008). La fila no porta cap dada
      personal pròpia: l'esborrat RGPD anonimitza la persona i les dades de la sol·licitud
      (T-M01-22, 028) i aquesta fila queda com a prova sense identificar ningú.
    """

    class AcceptedBy(models.TextChoices):
        APPLICANT = "applicant", _("Sol·licitant")
        GUARDIAN = "guardian", _("Pare, mare o tutor legal")

    request = models.ForeignKey(
        MemberRequest,
        on_delete=models.PROTECT,
        related_name="acceptances",
        verbose_name=_("sol·licitud"),
    )
    legal_text = models.ForeignKey(
        "core.LegalText", on_delete=models.PROTECT, related_name="+", verbose_name=_("text")
    )
    accepted_by = models.CharField(_("qui accepta"), max_length=10, choices=AcceptedBy.choices)
    channel = models.CharField(_("canal"), max_length=10, choices=MemberRequest.Channel.choices)
    recorded_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("registrat per"),
    )
    created_at = models.DateTimeField(_("data i hora"), default=timezone.now)

    class Meta:
        verbose_name = _("acceptació de l'alta")
        verbose_name_plural = _("acceptacions de l'alta")
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(accepted_by__in=["applicant", "guardian"]),
                name="joinacceptance_accepted_by_valid",
            ),
            models.CheckConstraint(
                condition=Q(channel="web", recorded_by__isnull=True)
                | Q(channel="in_person", recorded_by__isnull=False),
                name="joinacceptance_recorder_by_channel",
            ),
            models.UniqueConstraint(
                fields=["request", "legal_text"], name="joinacceptance_one_per_text"
            ),
        ]

    def __str__(self):
        return f"{self.request_id} {self.legal_text_id} {self.accepted_by}"


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


class AnnualFeeQuerySet(UndeletableQuerySet):
    # Se saltarien la comprovació de `AnnualFee.save` (persona i tipus del càrrec).
    def bulk_create(self, *args, **kwargs):
        raise ValidationError(_("Les quotes es creen d'una en una."))

    def update(self, **kwargs):
        raise ValidationError(_("Les quotes no es modifiquen en bloc."))


class AnnualFee(UndeletableModel):
    """Quota d'un soci sobre un càrrec de la 00 (RN-M01-51: no s'esborra). L'import i l'estat
    són els del càrrec. La generació i el venciment (P-29) són de la T-M01-14 i la T-M01-18.

    Que el càrrec sigui de la persona del soci i de tipus «quota» (M01-6) no ho comprova la base
    de dades (caldrien columnes duplicades aquí i una restricció nova al `Charge` de la 00): ho
    comprova `save` (T-M01-14, lectura de la 060), i el gestor no admet `bulk_create` ni `update`,
    que se'l saltarien. Una escriptura amb SQL directa no queda coberta."""

    class Kind(models.TextChoices):
        ANNUAL = "annual", _("Quota anual")
        TYPE_CHANGE_SUPPLEMENT = "type_change_supplement", _("Suplement de canvi de tipus")

    objects = AnnualFeeQuerySet.as_manager()

    member = models.ForeignKey(
        Member, on_delete=models.PROTECT, related_name="fees", verbose_name=_("soci")
    )
    period = models.PositiveSmallIntegerField(_("període"))
    kind = models.CharField(_("tipus de quota"), max_length=25, choices=Kind.choices)
    # P-54, sortida E (072): si la quota d'un període es va anul·lar, se'n crea una de nova del
    # mateix període amb el número d'ordre següent; l'anul·lada es queda a l'historial.
    sequence = models.PositiveSmallIntegerField(_("número d'ordre"), default=1)
    charge = models.OneToOneField(
        Charge, on_delete=models.PROTECT, related_name="annual_fee", verbose_name=_("càrrec")
    )
    due_on = models.DateField(_("venciment"))

    class Meta:
        verbose_name = _("quota")
        verbose_name_plural = _("quotes")
        constraints = [
            models.UniqueConstraint(
                fields=["member", "period", "kind", "sequence"],
                name="annualfee_unique_period_kind_sequence",
            ),
            models.CheckConstraint(
                condition=Q(sequence__gte=1), name="annualfee_sequence_positive"
            ),
            models.CheckConstraint(
                condition=Q(kind__in=["annual", "type_change_supplement"]),
                name="annualfee_kind_valid",
            ),
        ]

    def save(self, *args, **kwargs):
        charge = Charge.objects.only("person_id", "kind").get(pk=self.charge_id)
        if charge.kind != Charge.Kind.FEE:
            raise ValidationError(_("El càrrec d'una quota ha de ser del tipus «quota»."))
        if charge.person_id != Member.objects.values_list("person_id", flat=True).get(
            pk=self.member_id
        ):
            raise ValidationError(_("El càrrec d'una quota ha de ser de la persona del soci."))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.member_id} {self.period} {self.kind}"


class FeeExemption(AppendOnlyModel):
    """Exempció puntual d'una quota (T-M01-40; RN-M01-72 i RN-M01-94; decisió 085, J-2). El
    càrrec de la quota queda anul·lat amb la categoria «exempció» i aquesta fila diu quin període
    compta com a resolt: del venciment de la quota (la data d'aprovació en una alta, la de
    renovació en un soci que ja ho és) fins al mateix dia de l'any següent. No s'edita ni
    s'esborra; es desfà creant una quota nova del mateix període (P-54, sortida E). El motiu és
    al càrrec i al registre d'activitat, no aquí."""

    fee = models.OneToOneField(
        AnnualFee, on_delete=models.PROTECT, related_name="exemption", verbose_name=_("quota")
    )
    starts_on = models.DateField(_("inici del període eximit"))
    valid_until = models.DateField(_("vàlid fins al"))
    granted_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("compte que l'ha concedit"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("exempció de quota")
        verbose_name_plural = _("exempcions de quota")
        constraints = [
            models.CheckConstraint(
                condition=Q(valid_until__gt=F("starts_on")), name="feeexemption_period_valid"
            ),
        ]

    def __str__(self):
        return f"{self.fee_id} {self.starts_on}–{self.valid_until}"


class FeeReminder(models.Model):
    """Recordatori enviat d'una quota (T-M01-18; RN-M01-14, Q-061). Una fila per quota i dia:
    tornar a executar la tasca no envia el mateix recordatori dues vegades. Sense cap dada
    personal: el correu el registra la 00 (`OutgoingEmail`)."""

    fee = models.ForeignKey(
        AnnualFee, on_delete=models.PROTECT, related_name="reminders", verbose_name=_("quota")
    )
    offset_days = models.SmallIntegerField(_("dies respecte al venciment"))
    sent_on = models.DateField(_("data d'enviament"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("recordatori de quota")
        verbose_name_plural = _("recordatoris de quota")
        constraints = [
            models.UniqueConstraint(fields=["fee", "offset_days"], name="feereminder_unique_day")
        ]

    def __str__(self):
        return f"{self.fee_id} {self.offset_days:+d}"


class MemberCard(models.Model):
    """Carnet. Només es desa l'empremta del testimoni. El format de `token_hash` és el d'un
    SHA-256 en hexadecimal, però això no impedeix desar-hi un testimoni en clar que tingui
    aquest format: generar el testimoni i resumir-lo és del servei del carnet (T-M01-19).

    079 (RN-M01-85): el testimoni es calcula amb una clau del servidor a partir del soci i de
    `version`, i es torna a calcular per mostrar el QR; `key_id` diu amb quina clau. Cap secret
    es desa. `key_id` buit: carnet anterior a la 079 (testimoni aleatori), que es verifica igual
    però no es pot tornar a mostrar."""

    member = models.ForeignKey(
        Member, on_delete=models.PROTECT, related_name="cards", verbose_name=_("soci")
    )
    token_hash = models.CharField(_("empremta del testimoni"), max_length=64, unique=True)
    # Puja d'un en un per soci a cada emissió: un carnet reemès té un QR diferent.
    version = models.PositiveIntegerField(_("versió"), default=1)
    key_id = models.CharField(_("identificador de la clau"), max_length=8, blank=True, default="")
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
            models.UniqueConstraint(
                fields=["member", "version"], name="membercard_unique_version_per_member"
            ),
            models.CheckConstraint(
                condition=Q(version__gte=1) & Q(key_id__regex=r"^[a-z0-9]{0,8}$"),
                name="membercard_version_and_key_id_valid",
            ),
        ]

    def __str__(self):
        return f"{self.member_id} {self.issued_at:%Y-%m-%d}"


class LicenceRecord(models.Model):
    """Registre mínim de llicència (RN-M01-29). `expires_on` pot ser buit: caducitat
    desconeguda (addenda de la 058). `licence_type` és text lliure fins a la 06.
    `expiry_declared`: la data d'`expires_on` l'ha declarada el soci i la secretaria encara no
    l'ha confirmada; mentrestant no és vigent per a cap consumidor (RN-M01-77)."""

    class Source(models.TextChoices):
        MANUAL = "manual", _("Manual")
        CLUBER = "cluber", _("Cluber")

    member = models.ForeignKey(
        Member, on_delete=models.PROTECT, related_name="licence_records", verbose_name=_("soci")
    )
    licence_type = models.CharField(_("tipus de llicència"), max_length=100)
    issued_on = models.DateField(_("data d'alta"))
    expires_on = models.DateField(_("data de caducitat"), null=True, blank=True)
    expiry_declared = models.BooleanField(_("caducitat declarada pel soci"), default=False)
    source = models.CharField(_("origen"), max_length=10, choices=Source.choices)
    # Només als registres creats per un lot (T-M01-24); PROTECT protegeix el lot.
    import_batch = models.ForeignKey(
        "core.ImportBatch",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("lot d'importació"),
    )

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
            models.CheckConstraint(
                condition=Q(expiry_declared=False) | Q(expires_on__isnull=False),
                name="licencerecord_declared_has_expiry",
            ),
        ]

    def __str__(self):
        return f"{self.member_id} {self.licence_type}"
