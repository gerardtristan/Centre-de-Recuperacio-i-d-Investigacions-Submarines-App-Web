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
