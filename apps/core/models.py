from django.db import models
from django.db.models import Q

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
