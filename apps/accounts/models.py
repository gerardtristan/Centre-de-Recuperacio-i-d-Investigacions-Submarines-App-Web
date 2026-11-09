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
from django.utils.crypto import salted_hmac
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from apps.core.models import Person
from apps.core.normalization import normalize_email

validate_username = RegexValidator(
    r"^[a-z0-9][a-z0-9._-]{2,49}$",
    _(
        "El nom d'usuari ha de tenir entre 3 i 50 caràcters: lletres sense accents, xifres, "
        "punts, guions o guions baixos."
    ),
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
        account = self._save_new(account, password)
        # `is_superuser` no dona cap permís: el que compta és el rol administrador (059).
        from apps.core.roles import grant_initial_administrator

        grant_initial_administrator(account)
        return account

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
        PERSONAL = "personal", _("Personal")
        ADMIN = "admin", _("Administrador")

    class Status(models.TextChoices):
        PENDING = "pending", _("Pendent de verificar")
        ACTIVE = "active", _("Actiu")
        DISABLED = "disabled", _("Desactivat")

    # PROTECT: els comptes es desactiven, no s'esborren (RN-25).
    person = models.ForeignKey(
        Person, on_delete=models.PROTECT, related_name="accounts", verbose_name=_("persona")
    )
    kind = models.CharField(_("tipus"), max_length=10, choices=Kind.choices)
    # Correu d'entrada (personal) o nom d'usuari (administrador), sempre en minúscules.
    login = models.CharField(_("identificador d'entrada"), max_length=254, unique=True)
    notification_email = models.EmailField(_("correu de notificació"), blank=True)
    status = models.CharField(_("estat"), max_length=10, choices=Status.choices)
    is_emergency = models.BooleanField(_("és d'emergència"), default=False)
    # «Bloquejat temporalment» (V-01) no és un estat: un compte pendent també es pot bloquejar,
    # i el bloqueig s'acaba sol quan passa l'hora.
    failed_login_count = models.PositiveSmallIntegerField(_("intents fallits seguits"), default=0)
    locked_until = models.DateTimeField(_("bloquejat fins a"), null=True, blank=True)
    # Forma part de l'empremta de sessió: incrementar-lo tanca totes les sessions del compte
    # a la petició següent, en qualsevol dispositiu (RN-RP-11, RN-RP-20).
    session_epoch = models.PositiveIntegerField(default=0, editable=False)
    # Credencial temporal d'un restabliment per un altre administrador (HU-08, CA-08.1): mentre
    # n'hi ha, la contrasenya és temporal, caduca a aquesta hora (V-01) i s'ha de canviar en
    # entrar. Només en comptes d'administrador.
    password_temporary_until = models.DateTimeField(
        _("contrasenya temporal fins a"), null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AccountManager()

    USERNAME_FIELD = "login"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("compte")
        verbose_name_plural = _("comptes")
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
            # RN-16: el compte personal recupera per correu, mai amb una credencial temporal.
            models.CheckConstraint(
                condition=Q(kind="admin") | Q(password_temporary_until__isnull=True),
                name="account_temporary_password_admin_only",
            ),
        ]

    def __str__(self):
        return self.login

    @property
    def is_active(self):
        # Pendent o desactivat: no obté sessió.
        return self.status == self.Status.ACTIVE

    def _get_session_auth_hash(self, secret=None):
        key_salt = "apps.accounts.models.Account.get_session_auth_hash"
        return salted_hmac(
            key_salt, f"{self.password}:{self.session_epoch}", secret=secret, algorithm="sha256"
        ).hexdigest()

    def end_all_sessions(self):
        Account.objects.filter(pk=self.pk).update(session_epoch=F("session_epoch") + 1)
        self.refresh_from_db(fields=["session_epoch"])

    def is_locked(self, now):
        return self.locked_until is not None and self.locked_until > now

    @property
    def must_change_password(self):
        return self.password_temporary_until is not None

    def temporary_password_expired(self, now):
        return self.password_temporary_until is not None and self.password_temporary_until <= now

    @property
    def has_totp(self):
        device = getattr(self, "totp_device", None)
        return device is not None and device.confirmed_at is not None

    def clean(self):
        super().clean()
        self.login = normalize_login(self.login)
        if self.kind == self.Kind.PERSONAL:
            try:
                validate_email(self.login)
            except ValidationError:
                raise ValidationError(
                    {"login": gettext("El compte personal entra amb una adreça de correu vàlida.")}
                ) from None
            if self.notification_email or self.is_emergency or self.is_superuser:
                raise ValidationError(
                    gettext(
                        "El correu de notificació, l'emergència i el superusuari només són per a "
                        "comptes d'administrador."
                    )
                )
        elif self.kind == self.Kind.ADMIN:
            validate_username(self.login)

    def save(self, *args, **kwargs):
        self.login = normalize_login(self.login)
        self.notification_email = normalize_email(self.notification_email)
        super().save(*args, **kwargs)


class TotpDevice(models.Model):
    """Factor TOTP (RFC 6238), un per compte. El secret es guarda xifrat."""

    account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name="totp_device")
    secret_encrypted = models.TextField()
    # Null mentre l'alta no s'ha confirmat amb un codi vàlid.
    confirmed_at = models.DateTimeField(null=True, blank=True)
    # Últim interval acceptat: un codi no es pot fer servir dues vegades.
    last_used_step = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("factor TOTP")
        verbose_name_plural = _("factors TOTP")

    def __str__(self):
        return f"TOTP de {self.account}"


class RecoveryCode(models.Model):
    """Codi de recuperació d'un sol ús (HU-09). Només se'n guarda l'empremta."""

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="recovery_codes")
    code_hash = models.CharField(max_length=64, unique=True)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("codi de recuperació")
        verbose_name_plural = _("codis de recuperació")

    def __str__(self):
        return f"Codi de recuperació de {self.account}"


class EmailLinkRequest(models.Model):
    """Petició pública acceptada d'un enllaç pel correu (recuperació o reenviament de la
    verificació), per als límits de RN-M01-58 (`limits.py`). Les limitades per origen no es
    desen; les limitades per destinatari sí, perquè compten per a l'origen (066). Del
    destinatari només hi ha l'empremta, i només si s'ha posat el correu a la cua. S'esborren
    passades 24 hores (tasca diària).

    També hi van les sol·licituds del formulari «Fer-se soci» (T-M01-13), amb els seus propis
    llindars provisionals: no compten per als límits de RN-M01-58 ni al revés. I les consultes de
    la verificació pública del carnet (T-M01-20), només amb l'origen, per al límit de V-01."""

    class Purpose(models.TextChoices):
        RESET_PASSWORD = "reset", _("Recuperació de la contrasenya")
        VERIFY_EMAIL = "verify", _("Verificació del correu")
        JOIN = "join", _("Sol·licitud d'alta de soci")
        CARD_VERIFY = "card", _("Verificació del carnet")

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField()
    purpose = models.CharField(max_length=10, choices=Purpose.choices)
    recipient_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        verbose_name = _("petició d'enllaç pel correu")
        verbose_name_plural = _("peticions d'enllaç pel correu")
        indexes = [
            models.Index(fields=["ip_address", "created_at"], name="emaillink_ip_idx"),
            models.Index(
                fields=["recipient_hash", "purpose", "created_at"], name="emaillink_to_idx"
            ),
        ]

    def __str__(self):
        return f"{self.purpose} {self.created_at:%Y-%m-%d %H:%M}"


class FailedLogin(models.Model):
    """Intent d'entrada fallit, per al límit per origen (V-01, CA-07.6)."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField()
    # Null si l'identificador no correspon a cap compte d'aquesta entrada.
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)
    area = models.CharField(max_length=10)

    class Meta:
        verbose_name = _("intent fallit")
        verbose_name_plural = _("intents fallits")
        indexes = [models.Index(fields=["ip_address", "created_at"], name="failedlogin_ip_idx")]

    def __str__(self):
        return f"{self.ip_address} {self.created_at:%Y-%m-%d %H:%M}"
