"""Comptes d'accés (spec 00, RN-11 a RN-27; decisions 015, 018 i 029).

Hi ha dos tipus de compte, lligats al perfil únic de la persona:
- personal: entra per l'àrea de socis amb el correu, que és únic;
- administrador: entra per l'entrada d'administració amb un nom d'usuari únic; el seu correu
  només serveix per a notificacions i no és únic.

Els dos identificadors comparteixen la columna `login`. Un correu porta sempre «@» i un nom
d'usuari mai, de manera que una sola restricció d'unicitat compleix les dues regles.
Els rols i els permisos de gestió són dades de la 059 (T-RP-01), no grups de Django.
"""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, validate_email
from django.db import models, transaction
from django.db.models import F, Q
from django.db.models.functions import Lower

from apps.core.models import Person
from apps.core.normalization import normalize_email

validate_username = RegexValidator(
    r"^[a-z0-9][a-z0-9._-]{2,49}$",
    "El nom d'usuari ha de tenir entre 3 i 50 caràcters: lletres sense accents, xifres, "
    "punts, guions o guions baixos.",
)


def normalize_login(value: str) -> str:
    return (value or "").strip().lower()


class AccountManager(BaseUserManager):
    def get_by_natural_key(self, login):
        return self.get(login=normalize_login(login))

    def create_personal(self, person, email, password=None):
        """Compte personal: queda pendent fins que confirma el correu (RN-18)."""
        account = self.model(
            person=person,
            kind=Account.Kind.PERSONAL,
            login=normalize_email(email),
            status=Account.Status.PENDING,
        )
        return self._save_new(account, password)

    def create_admin(self, person, username, password=None, notification_email=""):
        """Compte d'administrador: no es verifica per correu (RN-19)."""
        account = self.model(
            person=person,
            kind=Account.Kind.ADMIN,
            login=normalize_login(username),
            notification_email=normalize_email(notification_email),
            status=Account.Status.ACTIVE,
        )
        return self._save_new(account, password)

    def create_user(self, login, password=None, *, person, **extra_fields):
        """Compatibilitat amb Django: el tipus es dedueix de l'identificador."""
        if "@" in (login or ""):
            return self.create_personal(person, login, password)
        return self.create_admin(person, login, password, **extra_fields)

    @transaction.atomic
    def create_superuser(self, login, password=None, *, person=None, **extra_fields):
        """Primer compte d'administrador (`createsuperuser`). Si no es dona la persona, se'n
        crea un perfil mínim amb el nom d'usuari, que s'ha de completar després."""
        if "@" in (login or ""):
            raise ValueError("Un compte d'administrador entra amb nom d'usuari, no amb correu.")
        if person is None:
            person = Person.objects.create(first_name=login, origin=Person.Origin.IN_PERSON)
        account = self.model(
            person=person,
            kind=Account.Kind.ADMIN,
            login=normalize_login(login),
            notification_email=normalize_email(extra_fields.pop("notification_email", "")),
            status=Account.Status.ACTIVE,
            is_superuser=True,
        )
        return self._save_new(account, password)

    def _save_new(self, account, password):
        if password:
            account.set_password(password)
        else:
            account.set_unusable_password()
        account.full_clean(exclude=["password"])
        account.save(using=self._db)
        return account


class Account(AbstractBaseUser, PermissionsMixin):
    class Kind(models.TextChoices):
        PERSONAL = "personal", "Personal"
        ADMIN = "admin", "Administrador"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendent de verificar"
        ACTIVE = "active", "Actiu"
        LOCKED = "locked", "Bloquejat temporalment"
        DISABLED = "disabled", "Desactivat"

    # PROTECT: els comptes es desactiven, no s'esborren (RN-25).
    person = models.ForeignKey(
        Person, on_delete=models.PROTECT, related_name="accounts", verbose_name="persona"
    )
    kind = models.CharField("tipus", max_length=10, choices=Kind.choices)
    # Correu d'entrada (personal) o nom d'usuari (administrador), sempre en minúscules.
    login = models.CharField("identificador d'entrada", max_length=254, unique=True)
    notification_email = models.EmailField("correu de notificació", blank=True)
    status = models.CharField("estat", max_length=10, choices=Status.choices)
    is_emergency = models.BooleanField("és d'emergència", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AccountManager()

    USERNAME_FIELD = "login"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "compte"
        verbose_name_plural = "comptes"
        constraints = [
            # Màxim un compte de cada tipus per persona (RN-13). L'excepció dels comptes
            # d'emergència depèn de Q-02, encara oberta.
            models.UniqueConstraint(fields=["person", "kind"], name="account_one_per_kind"),
            models.CheckConstraint(
                condition=Q(login=Lower(F("login"))), name="account_login_lowercase"
            ),
            # Personal: correu (amb «@»). Administrador: nom d'usuari (sense «@»).
            models.CheckConstraint(
                condition=Q(kind="personal", login__contains="@")
                | (Q(kind="admin") & ~Q(login__contains="@")),
                name="account_login_matches_kind",
            ),
            # Correu de notificació, emergència i superusuari només en comptes d'administrador.
            models.CheckConstraint(
                condition=Q(kind="admin")
                | Q(notification_email="", is_emergency=False, is_superuser=False),
                name="account_admin_only_fields",
            ),
        ]

    def __str__(self):
        return self.login

    @property
    def is_active(self):
        # Pendent, bloquejat o desactivat: no obté sessió.
        return self.status == self.Status.ACTIVE

    def clean(self):
        super().clean()
        self.login = normalize_login(self.login)
        if self.kind == self.Kind.PERSONAL:
            try:
                validate_email(self.login)
            except ValidationError:
                raise ValidationError(
                    {"login": "El compte personal entra amb una adreça de correu vàlida."}
                ) from None
            if self.notification_email or self.is_emergency or self.is_superuser:
                raise ValidationError(
                    "El correu de notificació, l'emergència i el superusuari només són per a "
                    "comptes d'administrador."
                )
        elif self.kind == self.Kind.ADMIN:
            validate_username(self.login)

    def save(self, *args, **kwargs):
        self.login = normalize_login(self.login)
        self.notification_email = normalize_email(self.notification_email)
        super().save(*args, **kwargs)
