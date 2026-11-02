import datetime

from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .normalization import normalize_document, normalize_email, normalize_phone


class Person(models.Model):
    """Perfil únic de qualsevol persona de qui el club guarda dades (spec 00, RN-01 a RN-10).

    Ser soci és una relació del mòdul 01: aquí no hi ha cap camp de soci, ni de salut, ni IBAN.
    """

    class DocumentType(models.TextChoices):
        DNI = "dni", "DNI"
        NIE = "nie", "NIE"
        PASSPORT = "passport", "Passaport"

    class Status(models.TextChoices):
        ACTIVE = "active", "Activa"
        ANONYMISED = "anonymised", "Anonimitzada"

    class Origin(models.TextChoices):
        IN_PERSON = "in_person", "Alta presencial"
        WEB = "web", "Web"
        GUEST = "guest", "Convidat"
        CLUBER_IMPORT = "cluber_import", "Importació de Cluber"

    first_name = models.CharField("nom", max_length=100)
    last_name = models.CharField("cognoms", max_length=150, blank=True)
    # No és únic: famílies que comparteixen correu (RN-10, V-05).
    contact_email = models.EmailField("correu de contacte", blank=True)
    phone = models.CharField("telèfon", max_length=30, blank=True)
    address = models.CharField("adreça", max_length=255, blank=True)
    id_document_type = models.CharField(
        "tipus de document", max_length=10, choices=DocumentType.choices, blank=True
    )
    id_document_number = models.CharField("número de document", max_length=30, blank=True)
    status = models.CharField("estat", max_length=12, choices=Status.choices, default=Status.ACTIVE)
    # Referència que substitueix la identitat en anonimitzar (decisió 028), p. ex. «A-0042».
    anonymous_ref = models.CharField(
        "referència anònima", max_length=20, null=True, blank=True, unique=True
    )
    origin = models.CharField("origen", max_length=16, choices=Origin.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "persona"
        verbose_name_plural = "persones"
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
        self.first_name = self.first_name.strip()
        self.last_name = self.last_name.strip()
        self.contact_email = normalize_email(self.contact_email)
        self.phone = normalize_phone(self.phone)
        self.id_document_number = normalize_document(self.id_document_number)
        super().save(*args, **kwargs)


class Role(models.Model):
    """Rol (decisió 059). Llista fixa, creada per migració: no es crea ni es reanomena des de
    l'app. Els rols de gestió s'assignen a comptes d'administrador; soci, visitant i convidat
    no són editables ni s'assignen."""

    class Code(models.TextChoices):
        INSTRUCTOR = "instructor", "Instructor"
        SECRETARY = "secretary", "Secretaria"
        COURSES_MANAGER = "courses_manager", "Responsable de cursos i sortides"
        EQUIPMENT_MANAGER = "equipment_manager", "Responsable de material"
        TREASURER = "treasurer", "Tresorer"
        HISTORY_DEPARTMENT = "history_department", "Departament d'Història"
        ADMINISTRATOR = "administrator", "Administrador"
        PRESIDENT = "president", "President"
        BOARD = "board", "Junta"
        COMMUNICATIONS_MANAGER = "communications_manager", "Responsable de comunicació"
        SHOP_MANAGER = "shop_manager", "Responsable de botiga"
        MEMBER = "member", "Soci"
        VISITOR = "visitor", "Visitant"
        GUEST = "guest", "Participant no soci"

    code = models.CharField(max_length=30, unique=True, choices=Code.choices)
    name = models.CharField(max_length=60)
    is_management = models.BooleanField()

    class Meta:
        verbose_name = "rol"
        verbose_name_plural = "rols"

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    """Cel·la editable de la matriu: el rol té el permís amb aquest abast. Els permisos
    protegits no tenen mai fila: els fixa el catàleg al codi (RN-RP-05)."""

    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="permissions")
    permission_code = models.CharField(max_length=80)
    scope = models.CharField(max_length=30)

    class Meta:
        verbose_name = "permís d'un rol"
        verbose_name_plural = "permisos dels rols"
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
        verbose_name = "rol d'un compte"
        verbose_name_plural = "rols dels comptes"
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
        verbose_name = "versió de la matriu de permisos"
        verbose_name_plural = "versions de la matriu de permisos"

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
    """

    class ActorKind(models.TextChoices):
        ACCOUNT = "account", "Compte"
        GUEST = "guest", "Convidat"
        SYSTEM = "system", "Sistema"
        # Ningú identificat: p. ex. un intent d'entrada amb un identificador desconegut.
        ANONYMOUS = "anonymous", "Sense identificar"

    created_at = models.DateTimeField("data i hora", default=timezone.now, db_index=True)
    actor_kind = models.CharField("tipus d'actor", max_length=10, choices=ActorKind.choices)
    actor_account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="compte que actua",
    )
    # La persona del compte o la convidada. En un esborrat RGPD queda anonimitzada (RN-89).
    actor_person = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="persona que actua",
    )
    # Rols de gestió actius del compte en aquell moment (RN-RP-15); buit si no en té.
    actor_roles = models.JSONField("rols actius", default=list, blank=True)
    # Sistema: nom de la tasca o del proveïdor. Convidat: identificador intern de l'enllaç,
    # mai el testimoni (CA-14.6).
    actor_origin = models.CharField("origen", max_length=100, blank=True)
    ip_address = models.GenericIPAddressField("adreça IP", null=True, blank=True)
    action = models.CharField("acció", max_length=60)
    target_type = models.CharField("tipus d'objecte", max_length=60, blank=True)
    target_id = models.CharField("identificador de l'objecte", max_length=64, blank=True)
    field = models.CharField("camp", max_length=60, blank=True)
    old_value = models.JSONField("valor anterior", null=True, blank=True, encoder=AuditJSONEncoder)
    new_value = models.JSONField("valor nou", null=True, blank=True, encoder=AuditJSONEncoder)
    reason = models.TextField("motiu", blank=True)
    details = models.JSONField("detalls", default=dict, blank=True, encoder=AuditJSONEncoder)

    class Meta:
        verbose_name = "entrada del registre d'activitat"
        verbose_name_plural = "registre d'activitat"
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
    dades i depenen de Q-16; aquí no se'n fixa cap."""

    kind = models.SlugField("tipus", max_length=40)
    version = models.PositiveIntegerField("versió")
    content = models.TextField("contingut")
    published_at = models.DateTimeField("vigent des de", default=timezone.now)
    published_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="publicat per",
    )

    class Meta:
        verbose_name = "text legal"
        verbose_name_plural = "textos legals"
        constraints = [
            models.UniqueConstraint(fields=["kind", "version"], name="legaltext_unique_version"),
        ]

    def __str__(self):
        return f"{self.kind} v{self.version}"


class Consent(AppendOnlyModel):
    """Atorgament o retirada d'un consentiment (RN-80, CA-17.1 i CA-17.3). Només s'hi afegeixen
    files: l'estat d'una persona per a un tipus és el de la seva última fila."""

    class Action(models.TextChoices):
        GRANTED = "granted", "Atorgat"
        WITHDRAWN = "withdrawn", "Retirat"

    class Channel(models.TextChoices):
        WEB = "web", "Web"
        IN_PERSON = "in_person", "Presencial"

    person = models.ForeignKey(
        Person, on_delete=models.PROTECT, related_name="consents", verbose_name="persona"
    )
    legal_text = models.ForeignKey(
        LegalText, on_delete=models.PROTECT, related_name="+", verbose_name="text acceptat"
    )
    action = models.CharField("acció", max_length=10, choices=Action.choices)
    channel = models.CharField("canal", max_length=10, choices=Channel.choices)
    # Compte que l'ha registrat, obligatori si és presencial (CA-17.1).
    recorded_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="registrat per",
    )
    created_at = models.DateTimeField("data i hora", default=timezone.now)

    class Meta:
        verbose_name = "consentiment"
        verbose_name_plural = "consentiments"
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(channel="in_person") | Q(recorded_by__isnull=False),
                name="consent_in_person_has_recorder",
            ),
        ]
        indexes = [models.Index(fields=["person", "created_at"], name="consent_person_idx")]

    def __str__(self):
        return f"{self.person_id} {self.legal_text} {self.action}"


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
        raise ValidationError("L'import ha de ser un enter positiu de cèntims.")


class Department(models.Model):
    """Departament o centre de cost (spec 00, HU-16, RN-62, RN-74, RN-75). La llista la fixa
    la junta (Q-17); d'inici només hi ha «General». Amb càrrecs no s'esborra (PROTECT): es
    desactiva."""

    GENERAL = "General"

    name = models.CharField("nom", max_length=80, unique=True)
    active = models.BooleanField("actiu", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "departament"
        verbose_name_plural = "departaments"

    def __str__(self):
        return self.name


class Charge(UndeletableModel):
    """Càrrec, estructura bàsica (spec 00, HU-15, RN-60 a RN-72; decisió 027). L'estat només
    canvia amb els serveis de `apps.core.charges`, que apliquen les transicions de RN-67."""

    class Kind(models.TextChoices):
        FEE = "fee", "Quota"
        ENROLMENT = "enrolment", "Inscripció"
        LICENCE = "licence", "Llicència"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendent"
        PAID = "paid", "Pagat"
        RETURNED = "returned", "Retornat"
        CANCELLED = "cancelled", "Anul·lat"

    person = models.ForeignKey(
        Person, on_delete=models.PROTECT, related_name="charges", verbose_name="persona deutora"
    )
    kind = models.CharField("tipus", max_length=10, choices=Kind.choices)
    concept = models.CharField("concepte", max_length=140)
    amount_cents = models.PositiveBigIntegerField("import (cèntims)")
    currency = models.CharField("moneda", max_length=3, default="EUR", editable=False)
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name="charges", verbose_name="departament"
    )
    status = models.CharField(
        "estat", max_length=10, choices=Status.choices, default=Status.PENDING
    )
    cancel_reason = models.TextField("motiu d'anul·lació", blank=True)
    # Mòdul que l'ha creat: «members», «activities», «licences»…
    origin = models.CharField("mòdul d'origen", max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "càrrec"
        verbose_name_plural = "càrrecs"
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
            raise ValidationError("Un departament desactivat no es pot triar per a càrrecs nous.")
        super().save(*args, **kwargs)


class Payment(UndeletableModel):
    """Pagament, estructura bàsica (spec 00, HU-15). El 05b l'amplia. Cap camp d'IBAN ni de
    targeta (RN-70, CA-15.6); els identificadors són del proveïdor, sense nom propi (043)."""

    class Method(models.TextChoices):
        DIRECT_DEBIT = "direct_debit", "Domiciliació"
        CARD = "card", "Targeta"
        BIZUM = "bizum", "Bizum"
        TRANSFER = "transfer", "Transferència"
        MANUAL = "manual", "Manual"

    charge = models.ForeignKey(
        Charge, on_delete=models.PROTECT, related_name="payments", verbose_name="càrrec"
    )
    method = models.CharField("mètode", max_length=12, choices=Method.choices)
    amount_cents = models.PositiveBigIntegerField("import (cèntims)")
    provider_status = models.CharField("estat al proveïdor", max_length=40, blank=True)
    needs_review = models.BooleanField("a revisar", default=False)
    provider_reference = models.CharField("referència del proveïdor", max_length=100, blank=True)
    transfer_reference = models.CharField("referència de transferència", max_length=60, blank=True)
    paid_at = models.DateTimeField("data del pagament", null=True, blank=True)
    # Registre manual (P-12, encara bloquejat): qui i per què.
    recorded_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="registrat per",
    )
    reason = models.TextField("motiu", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "pagament"
        verbose_name_plural = "pagaments"
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
            raise ValidationError("La domiciliació només s'admet per a quotes.")
        super().save(*args, **kwargs)
