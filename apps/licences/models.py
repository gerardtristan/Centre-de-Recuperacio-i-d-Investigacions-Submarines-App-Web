"""Llicències federatives (M06-6). Cap altra app escriu en aquests models: ho fa amb els serveis
del 06 (M06-8). Imports en cèntims; cap dada de salut ni de pagament (RN-M06-15)."""

import datetime
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from apps.core import business_settings
from apps.core.models import AppendOnlyModel, Charge, ImportBatch, Person, UndeletableModel


class ValidityRule(models.TextChoices):
    """RN-M06-01. La d'un dia només es fa servir si `licences.day_enabled` és activada
    (T-M06-19)."""

    CALENDAR_YEAR = "calendar_year", _("Any natural")
    DAYS_365 = "days_365", _("365 dies")
    SINGLE_DAY = "single_day", _("Un dia")


class LicenceType(models.Model):
    """Tipus de llicència de la federació (M06-6; RN-M06-01). La llista és una dada que
    mantenen el tresorer, el President i l'administrador (VC-38); no n'hi ha cap al codi."""

    class Category(models.TextChoices):
        AMATEUR = "amateur", _("Aficionat")
        TECHNICAL = "technical", _("Tècnic")
        OTHER = "other", _("Altres")

    name = models.CharField(_("nom"), max_length=80, unique=True)
    description = models.TextField(_("descripció"), blank=True)
    category = models.CharField(_("categoria"), max_length=9, choices=Category.choices)
    validity_rule = models.CharField(
        _("regla de validesa"), max_length=13, choices=ValidityRule.choices
    )
    active = models.BooleanField(_("actiu"), default=True)

    class Meta:
        verbose_name = _("tipus de llicència")
        verbose_name_plural = _("tipus de llicència")
        constraints = [
            models.CheckConstraint(
                condition=Q(category__in=["amateur", "technical", "other"]),
                name="licences_type_category_valid",
            ),
            models.CheckConstraint(
                condition=Q(validity_rule__in=["calendar_year", "days_365", "single_day"]),
                name="licences_type_validity_rule_valid",
            ),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        """CA-M06-21: cap tipus d'un dia actiu mentre `licences.day_enabled` és desactivada."""
        if (
            self.validity_rule == ValidityRule.SINGLE_DAY
            and self.active
            and not business_settings.get("licences.day_enabled")
        ):
            raise ValidationError(gettext("La llicència d'un dia no està activada."))


class LicencePrice(AppendOnlyModel):
    """Versió del preu d'un tipus (M06-6; RN-M06-05, 06, 08 i 18). Només s'hi afegeixen files:
    l'ORM ho impedeix i, a la base de dades, els activadors de la migració 0001. `valid_from` i
    `valid_to` són les dates d'inici de llicència a què s'aplica (els trams de l'any). El preu de
    soci és el de la federació (no hi ha cap camp per a un altre, RN-M06-05)."""

    class Kind(models.TextChoices):
        MEMBER = "member", _("Soci")
        NON_MEMBER = "non_member", _("No soci")

    licence_type = models.ForeignKey(
        LicenceType, on_delete=models.PROTECT, related_name="prices", verbose_name=_("tipus")
    )
    federation_cost_cents = models.PositiveIntegerField(_("preu de la federació (cèntims)"))
    non_member_surcharge_cents = models.PositiveIntegerField(_("recàrrec de no soci (cèntims)"))
    valid_from = models.DateField(_("vàlid des de"))
    valid_to = models.DateField(_("vàlid fins a"), null=True, blank=True)
    note = models.TextField(_("nota"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("creat per"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("preu de llicència")
        verbose_name_plural = _("preus de llicència")
        constraints = [
            models.CheckConstraint(
                condition=Q(federation_cost_cents__gt=0), name="licences_price_cost_positive"
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gte=models.F("valid_from")),
                name="licences_price_dates_ordered",
            ),
            models.CheckConstraint(
                condition=~Q(note__regex=r"^\s*$"), name="licences_price_note_required"
            ),
        ]

    def amount_cents(self, kind: str) -> int:
        """RN-M06-05 i RN-M06-06: soci = federació; no soci = federació + recàrrec."""
        if kind == self.Kind.MEMBER:
            return self.federation_cost_cents
        if kind == self.Kind.NON_MEMBER:
            return self.federation_cost_cents + self.non_member_surcharge_cents
        raise ValueError(f"Tipus de preu desconegut: «{kind}».")


IN_PROGRESS = ("requested", "paid", "filed")


class Licence(UndeletableModel):
    """Llicència d'una persona (M06-6). L'estat desat és el de RN-M06-09; el que es veu es
    deriva de les dates amb `display_status` (M06-5). En un esborrat RGPD s'anonimitza, no
    s'esborra (L-M06-06)."""

    class Status(models.TextChoices):
        REQUESTED = "requested", _("Sol·licitada")
        PAID = "paid", _("Pagada")
        FILED = "filed", _("Tramitada")
        ACTIVE = "active", _("Vigent")
        CANCELLED = "cancelled", _("Cancel·lada")
        LAPSED = "lapsed", _("No tramitada a temps")

    class Origin(models.TextChoices):
        CLUB = "club", _("Del club")
        EXTERNAL = "external", _("Ja en tenia una")
        IMPORTED_M01 = "imported_m01", _("Registre del 01")

    class Display(models.TextChoices):
        """Estat que es veu (M06-5)."""

        REQUESTED = "requested", _("Sol·licitada")
        PAID = "paid", _("Pagada")
        FILED = "filed", _("Tramitada")
        VALID = "valid", _("Vigent")
        TO_RENEW = "to_renew", _("Per renovar")
        EXPIRED = "expired", _("Caducada")
        NOT_STARTED = "not_started", _("Vigent més endavant")  # P-440
        UNCONFIRMED = "unconfirmed", _("Pendent de confirmar")  # RN-M06-24
        CANCELLED = "cancelled", _("Cancel·lada")
        LAPSED = "lapsed", _("No tramitada a temps")

    person = models.ForeignKey(
        Person, on_delete=models.PROTECT, related_name="licences", verbose_name=_("persona")
    )
    licence_type = models.ForeignKey(
        LicenceType, on_delete=models.PROTECT, related_name="licences", verbose_name=_("tipus")
    )
    # Còpia de la regla del tipus en demanar-la: canviar el tipus no canvia les ja demanades.
    validity_rule = models.CharField(
        _("regla de validesa"), max_length=13, choices=ValidityRule.choices
    )
    status = models.CharField(_("estat"), max_length=9, choices=Status.choices)
    origin = models.CharField(_("origen"), max_length=12, choices=Origin.choices)
    starts_on = models.DateField(_("inici"))
    # Buida si no se sap (RN-M06-24): només als registres del 01 «pendents de confirmar».
    expires_on = models.DateField(_("caducitat"), null=True, blank=True)
    # RN-M06-24: fals mentre la secretaria no hi posa (o confirma) la data. Cap avís ni
    # `licence.expired`, i `licences.current` la torna `unconfirmed`.
    expiry_confirmed = models.BooleanField(_("caducitat confirmada"), default=True)
    federation_number = models.CharField(_("número federatiu"), max_length=30, blank=True)
    price_kind = models.CharField(  # noqa: DJ001 (NULL = sense preu: origen extern o del 01)
        _("tipus de preu"), max_length=10, choices=LicencePrice.Kind.choices, null=True
    )
    price_cents = models.PositiveIntegerField(_("preu (cèntims)"), null=True)
    charge = models.OneToOneField(
        Charge,
        on_delete=models.PROTECT,
        null=True,
        related_name="licence",
        verbose_name=_("càrrec"),
    )
    renewal_of = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        related_name="renewals",
        verbose_name=_("renovació de"),
    )
    # Identificador del registre mínim del 01 (052, punt 8). No és cap clau forana: el 06 no
    # depèn dels models del 01.
    m01_record_ref = models.PositiveBigIntegerField(_("registre del 01"), null=True)
    import_batch = models.ForeignKey(
        ImportBatch,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
        verbose_name=_("lot d'importació"),
    )
    filed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="+"
    )
    filed_at = models.DateTimeField(null=True)
    activated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="+"
    )
    activated_at = models.DateTimeField(null=True)
    cancellation_reason = models.TextField(_("motiu de la cancel·lació"), blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="+"
    )
    # RN-M06-17 (054): puja en 1 a cada canvi, dins la mateixa transacció (`save`).
    version = models.PositiveIntegerField(_("versió"), default=1)
    # Quan es va emetre `licence.expired` (una sola vegada, T-M06-15).
    expired_at = models.DateTimeField(_("caducitat notificada el"), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("llicència")
        verbose_name_plural = _("llicències")
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=[*IN_PROGRESS, "active", "cancelled", "lapsed"]),
                name="licences_licence_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(origin__in=["club", "external", "imported_m01"]),
                name="licences_licence_origin_valid",
            ),
            models.CheckConstraint(
                condition=Q(validity_rule__in=["calendar_year", "days_365", "single_day"]),
                name="licences_licence_validity_rule_valid",
            ),
            models.CheckConstraint(
                condition=Q(expires_on__gte=models.F("starts_on")),
                name="licences_licence_dates_ordered",
            ),
            # RN-M06-09 i RN-M06-20: només una llicència d'un dia pot quedar «no tramitada a temps».
            models.CheckConstraint(
                condition=~Q(status="lapsed") | Q(validity_rule="single_day"),
                name="licences_licence_lapsed_only_single_day",
            ),
            models.CheckConstraint(
                condition=~Q(status="cancelled") | ~Q(cancellation_reason__regex=r"^\s*$"),
                name="licences_licence_cancel_has_reason",
            ),
            # Només les del club tenen preu i càrrec; les altres, mai (M06-6).
            models.CheckConstraint(
                condition=(
                    Q(origin="club", price_kind__isnull=False, price_cents__isnull=False)
                    | (
                        ~Q(origin="club")
                        & Q(price_kind__isnull=True, price_cents__isnull=True, charge__isnull=True)
                    )
                ),
                name="licences_licence_price_only_club",
            ),
            models.CheckConstraint(
                condition=Q(origin="imported_m01")
                | Q(m01_record_ref__isnull=True, import_batch__isnull=True),
                name="licences_licence_import_only_m01",
            ),
            # RN-M06-24: sense caducitat només una del pas únic «pendent de confirmar».
            models.CheckConstraint(
                condition=Q(expires_on__isnull=False) | Q(expiry_confirmed=False),
                name="licences_licence_no_expiry_unconfirmed",
            ),
            models.CheckConstraint(
                condition=Q(expiry_confirmed=True) | Q(origin="imported_m01", status="active"),
                name="licences_licence_unconfirmed_only_imported",
            ),
            # Una sola llicència anual en curs per persona i tipus; les d'un dia, per data
            # (RN-M06-19).
            models.UniqueConstraint(
                fields=["person", "licence_type"],
                condition=Q(status__in=IN_PROGRESS) & ~Q(validity_rule="single_day"),
                name="licences_licence_one_in_progress",
            ),
            models.UniqueConstraint(
                fields=["person", "licence_type", "starts_on"],
                condition=Q(status__in=IN_PROGRESS, validity_rule="single_day"),
                name="licences_licence_one_day_in_progress",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "expires_on"], name="licences_status_expires"),
            models.Index(fields=["person", "expires_on"], name="licences_person_expires"),
        ]

    def __str__(self):
        end = f"{self.expires_on:%d/%m/%Y}" if self.expires_on else "?"
        return f"{self.licence_type} ({self.starts_on:%d/%m/%Y}–{end})"

    def save(self, *args, **kwargs):
        """RN-M06-17: cada canvi d'una llicència ja desada puja la versió. Els serveis la
        bloquegen abans de canviar-la (`select_for_update`), i per això no es perd cap pujada."""
        if not self._state.adding:
            self.version += 1
            if kwargs.get("update_fields") is not None:
                kwargs["update_fields"] = {*kwargs["update_fields"], "version"}
        super().save(*args, **kwargs)

    def display_status(self, today: datetime.date, to_renew_days: int) -> str:
        """M06-5. `to_renew_days` és l'ajust `licences.to_renew_days`: el llegeix qui crida
        (l'ajust el crea la T-M06-20)."""
        if self.status != self.Status.ACTIVE:
            return self.status
        if not self.expiry_confirmed:
            return self.Display.UNCONFIRMED
        if self.expires_on < today:
            return self.Display.EXPIRED
        if self.starts_on > today:
            return self.Display.NOT_STARTED
        if (
            self.validity_rule != ValidityRule.SINGLE_DAY
            and (self.expires_on - today).days <= to_renew_days
        ):
            return self.Display.TO_RENEW
        return self.Display.VALID


class LicenceRefundProposal(models.Model):
    """Proposta de devolució d'una llicència cancel·lada després de pagar-la (M06-6; RN-M06-09,
    CA-M06-13). Cap devolució automàtica: el tresorer la fa (o la rebutja) i la devolució és la
    del 05b, amb `refund_key` com a clau perquè un reintent no torni dues vegades."""

    class Status(models.TextChoices):
        PROPOSED = "proposed", _("Proposada")
        DONE = "done", _("Feta")
        REJECTED = "rejected", _("Rebutjada")

    licence = models.OneToOneField(
        Licence, on_delete=models.PROTECT, related_name="refund_proposal",
        verbose_name=_("llicència"),
    )  # fmt: skip
    amount_cents = models.PositiveIntegerField(_("import (cèntims)"))
    reason = models.TextField(_("motiu"))
    status = models.CharField(
        _("estat"), max_length=8, choices=Status.choices, default=Status.PROPOSED
    )
    refund_key = models.UUIDField(_("clau de la devolució"), default=uuid.uuid4, unique=True)
    decision_note = models.TextField(_("nota de la decisió"), blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="+"
    )
    decided_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("proposta de devolució de llicència")
        verbose_name_plural = _("propostes de devolució de llicència")
        constraints = [
            models.CheckConstraint(
                condition=Q(amount_cents__gt=0), name="licences_refund_amount_positive"
            ),
            models.CheckConstraint(
                condition=Q(status__in=["proposed", "done", "rejected"]),
                name="licences_refund_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(status="proposed") | Q(decided_by__isnull=False),
                name="licences_refund_decided_has_author",
            ),
        ]

    def __str__(self):
        return f"{self.licence} · {self.get_status_display()}"


class LicenceReminder(AppendOnlyModel):
    """Avís de venciment enviat al titular (M06-6; RN-M06-12): un sol cop per llicència i tram."""

    licence = models.ForeignKey(Licence, on_delete=models.PROTECT, related_name="reminders")
    days_before = models.PositiveSmallIntegerField(_("dies abans"))
    sent_at = models.DateTimeField(_("enviat el"), auto_now_add=True)

    class Meta:
        verbose_name = _("avís de venciment")
        verbose_name_plural = _("avisos de venciment")
        constraints = [
            models.UniqueConstraint(
                fields=["licence", "days_before"], name="licences_reminder_once"
            )
        ]

    def __str__(self):
        return f"{self.licence} · {self.days_before}"


class LicenceReminderDigest(AppendOnlyModel):
    """Resum diari per a la secretaria (M06-6; RN-M06-12): un per dia i tram."""

    day = models.DateField(_("dia"))
    days_before = models.PositiveSmallIntegerField(_("dies abans"))
    count = models.PositiveIntegerField(_("llicències"))
    sent_to = models.PositiveIntegerField(_("destinataris"))
    sent_at = models.DateTimeField(_("enviat el"), auto_now_add=True)

    class Meta:
        verbose_name = _("resum d'avisos")
        verbose_name_plural = _("resums d'avisos")
        constraints = [
            models.UniqueConstraint(fields=["day", "days_before"], name="licences_digest_once")
        ]

    def __str__(self):
        return f"{self.day:%d/%m/%Y} · {self.days_before}"
