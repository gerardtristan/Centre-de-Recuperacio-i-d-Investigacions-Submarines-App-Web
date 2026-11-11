import datetime
import uuid

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from .normalization import normalize_document, normalize_email, normalize_phone


class Person(models.Model):
    """Perfil únic de qualsevol persona de qui el club guarda dades (spec 00, RN-01 a RN-10).

    Ser soci és una relació del mòdul 01: aquí no hi ha cap camp de soci, ni de salut, ni IBAN.
    """

    class DocumentType(models.TextChoices):
        DNI = "dni", _("DNI")
        NIE = "nie", _("NIE")
        PASSPORT = "passport", _("Passaport")

    class Status(models.TextChoices):
        ACTIVE = "active", _("Activa")
        ANONYMISED = "anonymised", _("Anonimitzada")

    class Origin(models.TextChoices):
        IN_PERSON = "in_person", _("Alta presencial")
        WEB = "web", _("Web")
        GUEST = "guest", _("Convidat")
        CLUBER_IMPORT = "cluber_import", _("Importació de Cluber")

    first_name = models.CharField(_("nom"), max_length=100)
    last_name = models.CharField(_("cognoms"), max_length=150, blank=True)
    # No és únic: famílies que comparteixen correu (RN-10, V-05).
    contact_email = models.EmailField(_("correu de contacte"), blank=True)
    phone = models.CharField(_("telèfon"), max_length=30, blank=True)
    address = models.CharField(_("adreça"), max_length=255, blank=True)
    # Camps opcionals del perfil (P-58, resolta per la 072): mai obligatoris per ser soci; la
    # finalitat de cadascun és a la política de privacitat (esborrany). Es conserven, s'exporten i
    # s'anonimitzen com la resta del perfil (Q-048; T-M01-22).
    landline = models.CharField(_("telèfon fix"), max_length=30, blank=True)
    postal_code = models.CharField(_("codi postal"), max_length=10, blank=True)
    city = models.CharField(_("població"), max_length=100, blank=True)
    province = models.CharField(_("província"), max_length=100, blank=True)
    id_document_type = models.CharField(
        "tipus de document", max_length=10, choices=DocumentType.choices, blank=True
    )
    id_document_number = models.CharField(_("número de document"), max_length=30, blank=True)
    # Opcional; buit = «sense data de naixement» (058, RN-M01-55). Només la llegeix qui té C1
    # (`members.field.birth_date`); la resta, `persons.age_band`. Mai en llistats, exportacions
    # (excepte RGPD i el llistat del 06) ni al registre d'activitat (RN-M01-48).
    birth_date = models.DateField(_("data de naixement"), null=True, blank=True)
    status = models.CharField(
        _("estat"), max_length=12, choices=Status.choices, default=Status.ACTIVE
    )
    # Referència que substitueix la identitat en anonimitzar (decisió 028), p. ex. «A-0042».
    anonymous_ref = models.CharField(
        "referència anònima", max_length=20, null=True, blank=True, unique=True
    )
    origin = models.CharField(_("origen"), max_length=16, choices=Origin.choices)
    # Només a les persones creades per un lot; mai a una de preexistent (T-M01-24). PROTECT
    # protegeix el lot, no la persona.
    import_batch = models.ForeignKey(
        "ImportBatch",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("lot d'importació"),
    )
    # Sense `choices`: les llengües actives són configuració (061). Es llegeix amb
    # `persons.language_for`, que torna al català si no és activa.
    preferred_language = models.CharField(_("llengua preferida"), max_length=7, default="ca")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("persona")
        verbose_name_plural = _("persones")
        constraints = [
            # Mateix document (normalitzat, amb el tipus) = mateixa persona (RN-06, V-03).
            models.UniqueConstraint(
                fields=["id_document_type", "id_document_number"],
                condition=~Q(id_document_number=""),
                name="person_unique_id_document",
            ),
            models.CheckConstraint(
                condition=Q(id_document_type="", id_document_number="")
                | (~Q(id_document_type="") & ~Q(id_document_number="")),
                name="person_id_document_type_and_number_together",
            ),
            models.CheckConstraint(
                condition=Q(status="active", anonymous_ref__isnull=True)
                | Q(status="anonymised", anonymous_ref__isnull=False),
                name="person_anonymous_ref_only_when_anonymised",
            ),
        ]
        indexes = [
            models.Index(fields=["contact_email"], name="person_contact_email_idx"),
            models.Index(fields=["last_name", "first_name"], name="person_name_idx"),
        ]

    def __str__(self):
        if self.status == self.Status.ANONYMISED:
            return self.anonymous_ref
        return f"{self.first_name} {self.last_name}".strip()

    def save(self, *args, **kwargs):
        self.normalize()
        super().save(*args, **kwargs)

    def normalize(self):
        # També el fa servir `persons.update` per saber què canvia abans de desar.
        self.first_name = self.first_name.strip()
        self.last_name = self.last_name.strip()
        self.contact_email = normalize_email(self.contact_email)
        self.phone = normalize_phone(self.phone)
        self.id_document_number = normalize_document(self.id_document_number)


class Role(models.Model):
    """Rol (decisió 059). Llista fixa, creada per migració: no es crea ni es reanomena des de
    l'app. Els rols de gestió s'assignen a comptes d'administrador; soci, visitant i convidat
    no són editables ni s'assignen."""

    class Code(models.TextChoices):
        INSTRUCTOR = "instructor", _("Instructor")
        SECRETARY = "secretary", _("Secretaria")
        COURSES_MANAGER = "courses_manager", _("Responsable de cursos i sortides")
        EQUIPMENT_MANAGER = "equipment_manager", _("Responsable de material")
        TREASURER = "treasurer", _("Tresorer")
        HISTORY_DEPARTMENT = "history_department", _("Departament d'Història")
        ADMINISTRATOR = "administrator", _("Administrador")
        PRESIDENT = "president", _("President")
        BOARD = "board", _("Junta")
        COMMUNICATIONS_MANAGER = "communications_manager", _("Responsable de comunicació")
        SHOP_MANAGER = "shop_manager", _("Responsable de botiga")
        MEMBER = "member", _("Soci")
        VISITOR = "visitor", _("Visitant")
        GUEST = "guest", _("Participant no soci")

    code = models.CharField(max_length=30, unique=True, choices=Code.choices)
    name = models.CharField(max_length=60)
    is_management = models.BooleanField()

    class Meta:
        verbose_name = _("rol")
        verbose_name_plural = _("rols")

    def __str__(self):
        # Decisió 061: l'etiqueta del codi es pot traduir; `name` queda com a dada interna.
        return str(self.get_code_display())


class RolePermission(models.Model):
    """Cel·la editable de la matriu: el rol té el permís amb aquest abast. Els permisos
    protegits no tenen mai fila: els fixa el catàleg al codi (RN-RP-05)."""

    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="permissions")
    permission_code = models.CharField(max_length=80)
    scope = models.CharField(max_length=30)

    class Meta:
        verbose_name = _("permís d'un rol")
        verbose_name_plural = _("permisos dels rols")
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission_code"], name="rolepermission_unique"
            ),
        ]

    def __str__(self):
        return f"{self.role.code}: {self.permission_code} ({self.scope})"


class AccountRole(models.Model):
    """Rol assignat a un compte d'administrador. Retirar-lo omple `removed_*`; la fila no
    s'esborra mai."""

    admin_account = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, related_name="role_assignments"
    )
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="assignments")
    assigned_by = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    removed_by = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    removed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("rol d'un compte")
        verbose_name_plural = _("rols dels comptes")
        constraints = [
            models.UniqueConstraint(
                fields=["admin_account", "role"],
                condition=Q(removed_at__isnull=True),
                name="accountrole_one_active",
            ),
        ]

    def __str__(self):
        return f"{self.admin_account}: {self.role.code}"


class PermissionMatrixVersion(models.Model):
    """Versió de la matriu (RN-RP-08). Només s'hi afegeixen files."""

    number = models.PositiveIntegerField(unique=True)
    changed_by = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField()
    # Llista de cel·les: {"role", "permission", "before", "after"} (abast o null).
    diff = models.JSONField(default=list)
    affected_accounts = models.JSONField(default=list)

    class Meta:
        verbose_name = _("versió de la matriu de permisos")
        verbose_name_plural = _("versions de la matriu de permisos")

    def __str__(self):
        return f"Matriu v{self.number}"


class AppendOnlyError(Exception):
    """Intent de modificar o esborrar una fila d'una taula on només s'afegeixen files (RN-51,
    RN-80; textos legals publicats)."""


_NO_CHANGE = "Aquest registre no es pot modificar ni esborrar: només s'hi afegeixen files."


class AppendOnlyQuerySet(models.QuerySet):
    # Les operacions en bloc no passen per `save` ni `delete` del model: també es bloquegen.
    def update(self, **kwargs):
        raise AppendOnlyError(_NO_CHANGE)

    def delete(self):
        raise AppendOnlyError(_NO_CHANGE)

    def bulk_update(self, objs, fields, batch_size=None):
        raise AppendOnlyError(_NO_CHANGE)

    def update_or_create(self, *args, **kwargs):
        raise AppendOnlyError(_NO_CHANGE)


class AppendOnlyModel(models.Model):
    objects = AppendOnlyQuerySet.as_manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise AppendOnlyError(_NO_CHANGE)
        # Sempre INSERT: amb una clau primària donada, Django provaria primer un UPDATE.
        kwargs["force_insert"] = True
        kwargs.pop("force_update", None)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AppendOnlyError(_NO_CHANGE)


class AuditJSONEncoder(DjangoJSONEncoder):
    """Com el de Django, però les dates i hores conserven els microsegons: un valor anterior
    del registre ha de ser exacte."""

    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        return super().default(o)


class AuditEntry(AppendOnlyModel):
    """Entrada del registre d'activitat (spec 00, HU-14, RN-50 a RN-53; RN-RP-15).

    Només s'hi afegeixen files: el model ho impedeix a l'ORM i uns disparadors de PostgreSQL
    (migració 0004) ho impedeixen a la base de dades, també amb SQL directe. Les entrades es
    creen amb els serveis de `apps.core.audit`, mai directament. Cap secret als valors (RN-52).
    Única excepció (RN-89, migració 0019): en un esborrat RGPD, `audit.substitute_identity`
    substitueix el que identifica la persona per la seva referència anònima.
    """

    class ActorKind(models.TextChoices):
        ACCOUNT = "account", _("Compte")
        GUEST = "guest", _("Convidat")
        SYSTEM = "system", _("Sistema")
        # Ningú identificat: p. ex. un intent d'entrada amb un identificador desconegut.
        ANONYMOUS = "anonymous", _("Sense identificar")

    created_at = models.DateTimeField(_("data i hora"), default=timezone.now, db_index=True)
    actor_kind = models.CharField(_("tipus d'actor"), max_length=10, choices=ActorKind.choices)
    actor_account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("compte que actua"),
    )
    # La persona del compte o la convidada. En un esborrat RGPD queda anonimitzada (RN-89).
    actor_person = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("persona que actua"),
    )
    # Rols de gestió actius del compte en aquell moment (RN-RP-15); buit si no en té.
    actor_roles = models.JSONField(_("rols actius"), default=list, blank=True)
    # Sistema: nom de la tasca o del proveïdor. Convidat: identificador intern de l'enllaç,
    # mai el testimoni (CA-14.6).
    actor_origin = models.CharField(_("origen"), max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(_("adreça IP"), null=True, blank=True)
    action = models.CharField(_("acció"), max_length=60)
    target_type = models.CharField(_("tipus d'objecte"), max_length=60, blank=True)
    target_id = models.CharField(_("identificador de l'objecte"), max_length=64, blank=True)
    field = models.CharField(_("camp"), max_length=60, blank=True)
    old_value = models.JSONField(
        _("valor anterior"), null=True, blank=True, encoder=AuditJSONEncoder
    )
    new_value = models.JSONField(_("valor nou"), null=True, blank=True, encoder=AuditJSONEncoder)
    reason = models.TextField(_("motiu"), blank=True)
    details = models.JSONField(_("detalls"), default=dict, blank=True, encoder=AuditJSONEncoder)

    class Meta:
        verbose_name = _("entrada del registre d'activitat")
        verbose_name_plural = _("registre d'activitat")
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(actor_kind="account", actor_account__isnull=False)
                | (~Q(actor_kind="account") & Q(actor_account__isnull=True) & Q(actor_roles=[])),
                name="auditentry_account_actor",
            ),
            models.CheckConstraint(
                condition=~Q(actor_kind__in=["system", "guest"]) | ~Q(actor_origin=""),
                name="auditentry_origin_for_system_and_guest",
            ),
            models.CheckConstraint(
                condition=~Q(actor_kind="guest") | Q(actor_person__isnull=False),
                name="auditentry_guest_has_person",
            ),
            models.CheckConstraint(
                condition=~Q(actor_kind="anonymous") | Q(actor_person__isnull=True),
                name="auditentry_anonymous_has_no_person",
            ),
        ]
        indexes = [
            models.Index(fields=["target_type", "target_id"], name="auditentry_target_idx"),
            models.Index(fields=["actor_account", "created_at"], name="auditentry_account_idx"),
            models.Index(fields=["action", "created_at"], name="auditentry_action_idx"),
        ]

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M:%S} {self.action}"


class LegalText(AppendOnlyModel):
    """Versió d'un text legal o de consentiment (spec 00, HU-17). Una versió publicada no es
    modifica: un canvi és una versió nova. Els tipus (privacitat, butlletí, imatge…) són
    dades i depenen de Q-16; aquí no se'n fixa cap. Una traducció és una fila més de la
    mateixa versió, no una versió nova (061)."""

    kind = models.SlugField(_("tipus"), max_length=40)
    version = models.PositiveIntegerField(_("versió"))
    language = models.CharField(_("llengua"), max_length=7, default="ca")
    content = models.TextField(_("contingut"))
    published_at = models.DateTimeField(_("vigent des de"), default=timezone.now)
    published_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("publicat per"),
    )

    class Meta:
        verbose_name = _("text legal")
        verbose_name_plural = _("textos legals")
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "version", "language"], name="legaltext_unique_version_language"
            ),
        ]

    def __str__(self):
        return f"{self.kind} v{self.version} ({self.language})"


class Consent(AppendOnlyModel):
    """Atorgament o retirada d'un consentiment (RN-80, CA-17.1 i CA-17.3). Només s'hi afegeixen
    files: l'estat d'una persona per a un tipus és el de la seva última fila."""

    class Action(models.TextChoices):
        GRANTED = "granted", _("Atorgat")
        WITHDRAWN = "withdrawn", _("Retirat")

    class Channel(models.TextChoices):
        WEB = "web", _("Web")
        IN_PERSON = "in_person", _("Presencial")
        # El consentiment ve de l'exportació de Cluber (071, punt 15; T-M01-25).
        CLUBER = "cluber", _("Importat de Cluber")

    class GivenBy(models.TextChoices):
        # Els mateixos valors que `members.JoinAcceptance.AcceptedBy`, vist des de la persona.
        PERSON = "person", _("La mateixa persona")
        GUARDIAN = "guardian", _("Pare, mare o tutor legal")

    person = models.ForeignKey(
        Person, on_delete=models.PROTECT, related_name="consents", verbose_name=_("persona")
    )
    # Qui el dona (T-M01-41): el representant només per al consentiment d'imatges d'un menor de
    # 14 anys donat a l'alta (072, Q-044 opció A, l'única excepció).
    given_by = models.CharField(
        _("qui el dona"), max_length=10, choices=GivenBy.choices, default=GivenBy.PERSON
    )
    legal_text = models.ForeignKey(
        LegalText, on_delete=models.PROTECT, related_name="+", verbose_name=_("text acceptat")
    )
    action = models.CharField(_("acció"), max_length=10, choices=Action.choices)
    channel = models.CharField(_("canal"), max_length=10, choices=Channel.choices)
    # Compte que l'ha registrat, obligatori si és presencial (CA-17.1).
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
        verbose_name = _("consentiment")
        verbose_name_plural = _("consentiments")
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(channel="in_person") | Q(recorded_by__isnull=False),
                name="consent_in_person_has_recorder",
            ),
            models.CheckConstraint(
                condition=Q(given_by__in=["person", "guardian"]), name="consent_given_by_valid"
            ),
        ]
        indexes = [models.Index(fields=["person", "created_at"], name="consent_person_idx")]

    def __str__(self):
        return f"{self.person_id} {self.legal_text} {self.action}"


class ErasureRequest(models.Model):
    """Sol·licitud d'esborrat de les dades d'una persona (P-M01-F, passos 3 a 5; RN-M01-57;
    T-M01-22). La crea la persona des del perfil (`erasure.request_erasure`) i l'atén qui té M11
    a `/gestio/rgpd/` (`erasure.approve` i `erasure.reject`). Aprovar-la l'executa a la mateixa
    transacció: «aprovada» només es veu si mai l'execució passa a la cua. Cap dada personal
    duplicada: la persona i els comptes són referències. `executed_at` és la data des d'on es
    comptarà el termini de conservació de les dades bloquejades quan es decideixi (Q-14)."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Pendent")
        APPROVED = "approved", _("Aprovada")
        REJECTED = "rejected", _("Rebutjada")
        EXECUTED = "executed", _("Executada")

    class Channel(models.TextChoices):
        WEB = "web", _("Web")

    person = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,
        related_name="erasure_requests",
        verbose_name=_("persona"),
    )
    requested_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("demanada pel compte"),
    )
    status = models.CharField(
        _("estat"), max_length=10, choices=Status.choices, default=Status.PENDING
    )
    channel = models.CharField(_("canal"), max_length=10, choices=Channel.choices)
    created_at = models.DateTimeField(_("data i hora"), default=timezone.now)
    # Qui l'aprova o la rebutja, i quan. Mai la mateixa persona que la demana (`erasure`).
    resolved_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("resolta per"),
    )
    resolved_at = models.DateTimeField(_("resolta el"), null=True, blank=True)
    # Text lliure de qui la rebutja: la persona continua activa i el pot demanar.
    rejection_reason = models.TextField(_("motiu del rebuig"), blank=True)
    executed_at = models.DateTimeField(_("executada el"), null=True, blank=True)

    class Meta:
        verbose_name = _("sol·licitud d'esborrat")
        verbose_name_plural = _("sol·licituds d'esborrat")
        constraints = [
            # Una sola pendent per persona.
            models.UniqueConstraint(
                fields=["person"],
                condition=Q(status="pending"),
                name="erasure_request_one_pending_per_person",
            ),
            models.CheckConstraint(
                condition=Q(status__in=["pending", "approved", "rejected", "executed"]),
                name="erasure_request_status_valid",
            ),
            # Pendent: ningú l'ha resolta. La resta: qui i quan.
            models.CheckConstraint(
                condition=Q(status="pending", resolved_by__isnull=True, resolved_at__isnull=True)
                | (~Q(status="pending") & Q(resolved_by__isnull=False, resolved_at__isnull=False)),
                name="erasure_request_resolved_pair",
            ),
            models.CheckConstraint(
                condition=Q(status="rejected", rejection_reason__regex=r"\S")
                | (~Q(status="rejected") & Q(rejection_reason="")),
                name="erasure_request_reason_only_when_rejected",
            ),
            models.CheckConstraint(
                condition=Q(status="executed", executed_at__isnull=False)
                | (~Q(status="executed") & Q(executed_at__isnull=True)),
                name="erasure_request_executed_at_only_when_executed",
            ),
        ]

    def __str__(self):
        return f"{self.person_id} {self.status}"


class UndeletableError(Exception):
    """Intent d'esborrar un registre econòmic: es corregeix amb una anul·lació (RN-61)."""


class UndeletableQuerySet(models.QuerySet):
    def delete(self):
        raise UndeletableError("Els registres econòmics no s'esborren: s'anul·len amb motiu.")


class UndeletableModel(models.Model):
    objects = UndeletableQuerySet.as_manager()

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        raise UndeletableError("Els registres econòmics no s'esborren: s'anul·len amb motiu.")


def validate_cents(value) -> None:
    """RN-60: enter positiu de cèntims. `bool` és un `int` a Python: es rebutja a part."""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValidationError(gettext("L'import ha de ser un enter positiu de cèntims."))


class Department(models.Model):
    """Departament o centre de cost (spec 00, HU-16, RN-62, RN-74, RN-75). La llista la fixa
    la junta (Q-17); d'inici només hi ha «General». Amb càrrecs no s'esborra (PROTECT): es
    desactiva."""

    GENERAL = "General"

    name = models.CharField(_("nom"), max_length=80, unique=True)
    active = models.BooleanField(_("actiu"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("departament")
        verbose_name_plural = _("departaments")

    def __str__(self):
        return self.name


class Charge(UndeletableModel):
    """Càrrec, estructura bàsica (spec 00, HU-15, RN-60 a RN-72; decisió 027). L'estat només
    canvia amb els serveis de `apps.core.charges`, que apliquen les transicions de RN-67."""

    class Kind(models.TextChoices):
        FEE = "fee", _("Quota")
        ENROLMENT = "enrolment", _("Inscripció")
        LICENCE = "licence", _("Llicència")

    class Status(models.TextChoices):
        PENDING = "pending", _("Pendent")
        PAID = "paid", _("Pagat")
        RETURNED = "returned", _("Retornat")
        CANCELLED = "cancelled", _("Anul·lat")

    person = models.ForeignKey(
        Person, on_delete=models.PROTECT, related_name="charges", verbose_name=_("persona deutora")
    )
    kind = models.CharField(_("tipus"), max_length=10, choices=Kind.choices)
    concept = models.CharField(_("concepte"), max_length=140)
    amount_cents = models.PositiveBigIntegerField(_("import (cèntims)"))
    currency = models.CharField(_("moneda"), max_length=3, default="EUR", editable=False)
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name="charges", verbose_name=_("departament")
    )
    status = models.CharField(
        "estat", max_length=10, choices=Status.choices, default=Status.PENDING
    )
    cancel_reason = models.TextField(_("motiu d'anul·lació"), blank=True)
    # Mòdul que l'ha creat: «members», «activities», «licences»…
    origin = models.CharField(_("mòdul d'origen"), max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("càrrec")
        verbose_name_plural = _("càrrecs")
        constraints = [
            models.CheckConstraint(condition=Q(amount_cents__gt=0), name="charge_amount_positive"),
            models.CheckConstraint(condition=Q(currency="EUR"), name="charge_currency_eur"),
            models.CheckConstraint(
                condition=Q(kind__in=["fee", "enrolment", "licence"]), name="charge_kind_valid"
            ),
            models.CheckConstraint(
                condition=Q(status__in=["pending", "paid", "returned", "cancelled"]),
                name="charge_status_valid",
            ),
            models.CheckConstraint(
                condition=~Q(status="cancelled") | ~Q(cancel_reason=""),
                name="charge_cancel_has_reason",
            ),
        ]
        indexes = [models.Index(fields=["person", "status"], name="charge_person_status_idx")]

    def __str__(self):
        return f"{self.get_kind_display()} {self.amount_cents} c ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        validate_cents(self.amount_cents)
        if self._state.adding and not self.department.active:
            raise ValidationError(
                gettext("Un departament desactivat no es pot triar per a càrrecs nous.")
            )
        super().save(*args, **kwargs)


class Payment(UndeletableModel):
    """Pagament, estructura bàsica (spec 00, HU-15). El 05b l'amplia. Cap camp d'IBAN ni de
    targeta (RN-70, CA-15.6); els identificadors són del proveïdor, sense nom propi (043)."""

    class Method(models.TextChoices):
        DIRECT_DEBIT = "direct_debit", _("Domiciliació")
        CARD = "card", _("Targeta")
        BIZUM = "bizum", _("Bizum")
        TRANSFER = "transfer", _("Transferència")
        MANUAL = "manual", _("Manual")

    charge = models.ForeignKey(
        Charge, on_delete=models.PROTECT, related_name="payments", verbose_name=_("càrrec")
    )
    method = models.CharField(_("mètode"), max_length=12, choices=Method.choices)
    amount_cents = models.PositiveBigIntegerField(_("import (cèntims)"))
    provider_status = models.CharField(_("estat al proveïdor"), max_length=40, blank=True)
    needs_review = models.BooleanField(_("a revisar"), default=False)
    provider_reference = models.CharField(_("referència del proveïdor"), max_length=100, blank=True)
    transfer_reference = models.CharField(
        _("referència de transferència"), max_length=60, blank=True
    )
    paid_at = models.DateTimeField(_("data del pagament"), null=True, blank=True)
    # Registre manual (P-12, encara bloquejat): qui i per què.
    recorded_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("registrat per"),
    )
    reason = models.TextField(_("motiu"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("pagament")
        verbose_name_plural = _("pagaments")
        constraints = [
            models.CheckConstraint(condition=Q(amount_cents__gt=0), name="payment_amount_positive"),
            models.CheckConstraint(
                condition=Q(method__in=["direct_debit", "card", "bizum", "transfer", "manual"]),
                name="payment_method_valid",
            ),
        ]

    def __str__(self):
        return f"{self.get_method_display()} {self.amount_cents} c"

    def save(self, *args, **kwargs):
        validate_cents(self.amount_cents)
        # RN-69: la domiciliació només per a pagaments recurrents (quotes).
        if self.method == self.Method.DIRECT_DEBIT and self.charge.kind != Charge.Kind.FEE:
            raise ValidationError(gettext("La domiciliació només s'admet per a quotes."))
        super().save(*args, **kwargs)


class OutgoingEmail(models.Model):
    """Registre d'enviaments (spec 00, annex A, RN-A7): plantilla, destinatari, llengua, estat
    i data. Es crea en posar el correu a la cua (`mail.queue_email`).

    El cos només es guarda mentre el correu espera: s'esborra quan s'ha enviat bé o quan
    s'esgoten els intents, perquè pot portar enllaços d'un sol ús (RN-A12). Mai cap adjunt.
    """

    class Status(models.TextChoices):
        QUEUED = "queued", _("A la cua")
        SENT = "sent", _("Enviat")
        FAILED = "failed", _("Fallit")

    template = models.CharField(_("plantilla"), max_length=100)
    # Llengua amb què s'ha generat (061, punt 7): la de la plantilla que s'ha fet servir.
    language = models.CharField(_("llengua"), max_length=7)
    to_address = models.EmailField(_("destinatari"))
    person = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("persona"),
    )
    subject = models.CharField(_("assumpte"), max_length=255)
    body_text = models.TextField(_("cos (text)"), blank=True)
    body_html = models.TextField(_("cos (HTML)"), blank=True)
    status = models.CharField(
        _("estat"), max_length=8, choices=Status.choices, default=Status.QUEUED
    )
    attempts = models.PositiveSmallIntegerField(_("intents"), default=0)
    # Només el tipus d'error i un tros del missatge del servidor, mai el cos.
    last_error = models.CharField(_("darrer error"), max_length=255, blank=True)
    created_at = models.DateTimeField(_("posat a la cua"), auto_now_add=True)
    sent_at = models.DateTimeField(_("enviat"), null=True, blank=True)

    class Meta:
        verbose_name = _("correu enviat")
        verbose_name_plural = _("correus enviats")
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=["queued", "sent", "failed"]),
                name="outgoing_email_status_valid",
            ),
            # Un correu que ja no espera no guarda el cos.
            models.CheckConstraint(
                condition=Q(status="queued") | Q(body_text="", body_html=""),
                name="outgoing_email_body_only_while_queued",
            ),
            models.CheckConstraint(
                condition=Q(status="sent", sent_at__isnull=False)
                | (~Q(status="sent") & Q(sent_at__isnull=True)),
                name="outgoing_email_sent_at_only_when_sent",
            ),
        ]
        indexes = [models.Index(fields=["status", "created_at"], name="outgoing_email_status_idx")]

    def __str__(self):
        return f"{self.template} ({self.get_status_display()})"


class PrivateFile(models.Model):
    """Fitxer privat (spec 00, annex B; decisió 005). El contingut és a l'emmagatzematge
    «private» (Scaleway a producció); aquí només hi ha qui n'és el propietari i com es diu.

    Identificador i clau aleatoris: cap nom previsible ni cap dada personal a la ruta. Hereta el
    permís del seu propietari (RN-B4): el comprova `files.can_access`.
    """

    class Kind(models.TextChoices):
        GDPR_EXPORT = "gdpr_export", _("Exportació de dades (RGPD)")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    storage_key = models.CharField(_("clau a l'emmagatzematge"), max_length=100, unique=True)
    kind = models.CharField(_("tipus"), max_length=20, choices=Kind.choices)
    owner = models.ForeignKey(
        Person, on_delete=models.PROTECT, related_name="+", verbose_name=_("propietari")
    )
    content_type = models.CharField(_("tipus de contingut"), max_length=100)
    size_bytes = models.PositiveBigIntegerField(_("mida (bytes)"))
    # Nom que rep qui el descarrega; el posa el codi, mai l'usuari.
    download_name = models.CharField(_("nom de descàrrega"), max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    # Després d'aquesta data, la tasca diària l'esborra (V-08: exportació RGPD, 7 dies).
    expires_at = models.DateTimeField(_("caduca"), null=True, blank=True)
    deleted_at = models.DateTimeField(_("esborrat"), null=True, blank=True)

    class Meta:
        verbose_name = _("fitxer privat")
        verbose_name_plural = _("fitxers privats")
        constraints = [
            models.CheckConstraint(
                condition=Q(kind__in=["gdpr_export"]), name="private_file_kind_valid"
            ),
        ]
        indexes = [models.Index(fields=["expires_at"], name="private_file_expires_idx")]

    def __str__(self):
        return f"{self.get_kind_display()} {self.pk}"


# Codis de fila d'una línia d'importació: llista tancada, comprovada a la base de dades, perquè
# cap línia no desi text lliure (T-M01-24). Un codi nou necessita una migració.
IMPORT_LINE_CODES = (
    # Errors
    "field_count",
    "field_too_long",
    "member_number_invalid",
    "email_invalid",
    "duplicate_document",
    "duplicate_member_number",
    "identity_conflict",
    "member_number_unavailable",
    "date_invalid",  # 071 (T-M01-25)
    # Advertiments
    "member_number_leading_zeros",
    "match_without_document_type",
    "total_price_differs",  # 071 (T-M01-25)
    # Exclusions automàtiques
    "left_in_cluber",  # 072, Q-071
    # Dades pendents
    "member_type",
    "member_status",
    "joined_on",
    "id_document_type",
    "member_number",
    "first_name",
    "last_name",
    "id_document",
    "email",
    "phone",
)


class ImportBatch(UndeletableModel):
    """Lot d'importació (spec 00; contracte compartit de la T-M01-24).

    Conserva els quatre estats de la spec 00. Les transicions les controlen els serveis de cada
    tasca: en el recorregut de Cluber, el lot només es crea en confirmar i neix confirmat
    (T-M01-25); quins estats fa servir l'extracte bancari ho decideix la T-M00-01. No es pot
    esborrar, però tampoc no és de només afegir files. Els recomptes no tenen cap restricció de
    suma: les seves categories no són excloents.
    """

    class Kind(models.TextChoices):
        CLUBER = "cluber", _("Cluber")
        BANK_STATEMENT = "bank_statement", _("Extracte bancari")

    class Status(models.TextChoices):
        PREVIEW = "preview", _("Previsualització")
        CONFIRMED = "confirmed", _("Confirmat")
        UNDONE = "undone", _("Desfet")
        REJECTED = "rejected", _("Rebutjat")

    kind = models.CharField(_("tipus"), max_length=20, choices=Kind.choices)
    status = models.CharField(_("estat"), max_length=10, choices=Status.choices)
    file_sha256 = models.CharField(_("empremta del fitxer"), max_length=64)
    created_by = models.ForeignKey(
        "accounts.Account", on_delete=models.PROTECT, related_name="+", verbose_name=_("creat per")
    )
    created_at = models.DateTimeField(_("creat el"), default=timezone.now)
    confirmed_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("confirmat per"),
    )
    confirmed_at = models.DateTimeField(_("confirmat el"), null=True, blank=True)
    undone_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("desfet per"),
    )
    undone_at = models.DateTimeField(_("desfet el"), null=True, blank=True)
    new_count = models.PositiveIntegerField(_("noves"), default=0)
    matching_count = models.PositiveIntegerField(_("coincidents"), default=0)
    error_count = models.PositiveIntegerField(_("amb error"), default=0)
    excluded_count = models.PositiveIntegerField(_("excloses"), default=0)
    duplicate_count = models.PositiveIntegerField(_("duplicades"), default=0)

    class Meta:
        verbose_name = _("lot d'importació")
        verbose_name_plural = _("lots d'importació")
        constraints = [
            models.CheckConstraint(
                condition=Q(kind__in=["cluber", "bank_statement"]), name="importbatch_kind_valid"
            ),
            models.CheckConstraint(
                condition=Q(status__in=["preview", "confirmed", "undone", "rejected"]),
                name="importbatch_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(file_sha256__regex=r"^[0-9a-f]{64}$"), name="importbatch_sha256_format"
            ),
            # Cada actor amb la seva data: tots dos o cap.
            models.CheckConstraint(
                condition=Q(confirmed_by__isnull=True, confirmed_at__isnull=True)
                | Q(confirmed_by__isnull=False, confirmed_at__isnull=False),
                name="importbatch_confirmed_pair",
            ),
            models.CheckConstraint(
                condition=Q(undone_by__isnull=True, undone_at__isnull=True)
                | Q(undone_by__isnull=False, undone_at__isnull=False),
                name="importbatch_undone_pair",
            ),
            # Quines dades porta cada estat (amb les parelles, n'hi ha prou amb les dates).
            models.CheckConstraint(
                condition=Q(
                    status__in=["preview", "rejected"],
                    confirmed_at__isnull=True,
                    undone_at__isnull=True,
                )
                | Q(status="confirmed", confirmed_at__isnull=False, undone_at__isnull=True)
                | Q(status="undone", confirmed_at__isnull=False, undone_at__isnull=False),
                name="importbatch_status_fields",
            ),
            models.CheckConstraint(
                condition=Q(confirmed_at__isnull=True)
                | Q(confirmed_at__gte=models.F("created_at")),
                name="importbatch_confirmed_after_created",
            ),
            models.CheckConstraint(
                condition=Q(undone_at__isnull=True) | Q(undone_at__gte=models.F("confirmed_at")),
                name="importbatch_undone_after_confirmed",
            ),
            # RN-93: un sol lot de Cluber confirmat (un de desfet no compta).
            models.UniqueConstraint(
                fields=["kind"],
                condition=Q(kind="cluber", status="confirmed"),
                name="importbatch_one_confirmed_cluber",
            ),
        ]

    def __str__(self):
        return f"{self.get_kind_display()} {self.pk} ({self.get_status_display()})"


def _array_int(function, *args):
    return models.Func(*args, function=function, output_field=models.IntegerField())


class ImportLine(UndeletableModel):
    """Línia d'un lot d'importació (spec 00; T-M01-24).

    Sense còpies dels valors personals del fitxer: fila, resultat, codis d'una llista tancada i,
    a les files noves i coincidents, la referència a la persona (que continua sent una dada
    personal). La procedència d'un registre la determina el seu `import_batch`, no aquesta
    referència. Sense JSON obert: les columnes tipades dels altres tipus d'importació les
    afegeixen les seves tasques.
    """

    class Result(models.TextChoices):
        NEW = "new", _("Nova")
        MATCHING = "matching", _("Coincident")
        ERROR = "error", _("Amb error")
        EXCLUDED = "excluded", _("Exclosa")
        DUPLICATE = "duplicate", _("Duplicada")

    batch = models.ForeignKey(
        ImportBatch, on_delete=models.PROTECT, related_name="lines", verbose_name=_("lot")
    )
    row = models.PositiveIntegerField(_("fila"))
    result = models.CharField(_("resultat"), max_length=10, choices=Result.choices)
    codes = ArrayField(models.CharField(max_length=40), default=list, verbose_name=_("codis"))
    # PROTECT protegeix la persona referenciada.
    person = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("persona"),
    )

    class Meta:
        verbose_name = _("línia d'importació")
        verbose_name_plural = _("línies d'importació")
        constraints = [
            models.UniqueConstraint(fields=["batch", "row"], name="importline_unique_row"),
            models.CheckConstraint(condition=Q(row__gte=1), name="importline_row_positive"),
            models.CheckConstraint(
                condition=Q(result__in=["new", "matching", "error", "excluded", "duplicate"]),
                name="importline_result_valid",
            ),
            models.CheckConstraint(
                condition=Q(result__in=["new", "matching"]) | Q(person__isnull=True),
                name="importline_person_only_new_or_matching",
            ),
            # Només codis de la llista; un element NULL no hi és mai contingut (<@).
            models.CheckConstraint(
                condition=Q(codes__contained_by=list(IMPORT_LINE_CODES)),
                name="importline_codes_closed_list",
            ),
            # Una llista d'una sola dimensió que comença a 1 (o buida): <@ no mira l'estructura.
            models.CheckConstraint(
                condition=Q(codes__len=0)
                | Q(
                    models.lookups.Exact(_array_int("array_ndims", "codes"), 1),
                    models.lookups.Exact(_array_int("array_lower", "codes", models.Value(1)), 1),
                ),
                name="importline_codes_one_dimension",
            ),
        ]

    def __str__(self):
        return f"{self.batch_id}:{self.row}"


class Setting(models.Model):
    """Valor de negoci configurable (decisió 055; planning.md, «peça comuna d'ajustos»).

    Cada mòdul declara els seus valors amb una migració de dades quan construeix la seva
    pantalla d'ajustos. Es llegeixen i es canvien només amb els serveis de
    `apps.core.business_settings`. Qui el pot canviar és el permís del catàleg
    `settings.edit.<clau>` (RN-RP-17 i RN-RP-19): no hi ha camp `editor_roles` (060).
    """

    class ValueType(models.TextChoices):
        INTEGER = "integer", _("Enter")
        CENTS = "cents", _("Import en cèntims")
        BOOLEAN = "boolean", _("Sí o no")
        TEXT = "text", _("Text")
        CHOICE = "choice", _("Opció")
        URL = "url", _("URL")
        DAY_MONTH = "day_month", _("Dia i mes")
        INTEGER_LIST = "integer_list", _("Llista d'enters")

    key = models.CharField(_("clau"), max_length=60, unique=True)
    module = models.CharField(_("mòdul"), max_length=30)
    value_type = models.CharField(_("tipus"), max_length=20, choices=ValueType.choices)
    initial_value = models.JSONField(_("valor inicial"))
    # Rang. Per a «dia i mes», el valor es guarda com a "MM-DD" i el rang com a MMDD (1001 =
    # 1 d'octubre). Per a la llista d'enters, el rang s'aplica a cada element.
    min_value = models.BigIntegerField(_("valor mínim"), null=True, blank=True)
    max_value = models.BigIntegerField(_("valor màxim"), null=True, blank=True)
    choices = models.JSONField(_("opcions"), default=list, blank=True)
    max_length = models.PositiveIntegerField(_("longitud màxima"), null=True, blank=True)
    affects_money = models.BooleanField(_("afecta diners"), default=False)
    effective_dated = models.BooleanField(_("amb data d'entrada en vigor"), default=False)

    class Meta:
        verbose_name = _("ajust")
        verbose_name_plural = _("ajustos")
        ordering = ["module", "key"]
        constraints = [
            # RN-AJ-03: un valor de diners sempre té data d'entrada en vigor.
            models.CheckConstraint(
                condition=Q(affects_money=False) | Q(effective_dated=True),
                name="setting_money_is_effective_dated",
            ),
            models.CheckConstraint(
                condition=Q(min_value__isnull=True)
                | Q(max_value__isnull=True)
                | Q(min_value__lte=models.F("max_value")),
                name="setting_range_ordered",
            ),
        ]

    def __str__(self):
        return self.key

    def clean(self):
        if not self.key.startswith(f"{self.module}."):
            raise ValidationError({"key": gettext("La clau ha de començar pel prefix del mòdul.")})
        from .business_settings import validate_value

        validate_value(self, self.initial_value)


class SettingVersion(AppendOnlyModel):
    """Canvi d'un ajust (RN-AJ-02). Només s'hi afegeixen files: el model ho impedeix a l'ORM i
    uns disparadors de PostgreSQL (migració 0012), a la base de dades."""

    setting = models.ForeignKey(
        Setting, on_delete=models.PROTECT, related_name="versions", verbose_name=_("ajust")
    )
    value = models.JSONField(_("valor"))
    # Buida si l'ajust no té data d'entrada en vigor.
    effective_from = models.DateField(_("en vigor des de"), null=True, blank=True)
    changed_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("compte que el canvia"),
    )
    changed_at = models.DateTimeField(_("data del canvi"), default=timezone.now)
    previous_value = models.JSONField(_("valor anterior"), null=True, blank=True)
    note = models.TextField(_("nota"), blank=True)

    class Meta:
        verbose_name = _("versió d'un ajust")
        verbose_name_plural = _("versions dels ajustos")
        ordering = ["setting", "changed_at", "id"]
        indexes = [models.Index(fields=["setting", "effective_from"])]

    def __str__(self):
        return f"{self.setting_id}:{self.effective_from or self.changed_at:%Y-%m-%d}"
