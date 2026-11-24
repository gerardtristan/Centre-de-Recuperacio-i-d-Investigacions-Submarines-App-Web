"""Models del 07 (M07-6). Cap camp guarda HTML: el text es desa tal qual i s'escapa en mostrar-lo
(RN-M07-10). Les llistes de plantilles, d'accents i de tipus de bloc són codi (M07-6, «Es queden
al codi»)."""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import AppendOnlyModel

from .routes import route_taken


class Page(models.Model):
    """Pàgina de la web. El que veu el públic és la seva última `PageVersion` (RN-M07-03)."""

    class Template(models.TextChoices):
        # P-590: la llista de plantilles; les tres últimes són les de l'editor (T-DX-36).
        BASIC = "basica", _("Bàsica")
        HOME = "portada", _("Portada")
        LIST = "llista", _("Activitats")
        BLOG = "blog", _("Notícies")

    class Accent(models.TextChoices):
        # Només tokens de `tokens.css` (els de l'editor, T-DX-36).
        ACCENT = "accent", _("Daurat")
        MARI = "mari", _("Marí")
        INFO = "info", _("Blau")

    class Status(models.TextChoices):
        DRAFT = "draft", _("Esborrany")
        PUBLISHED = "published", _("Publicada")
        RETIRED = "retired", _("Retirada")

    slug = models.SlugField(_("adreça"), max_length=60, unique=True)
    title = models.CharField(_("títol"), max_length=120)
    template = models.CharField(
        _("plantilla"), max_length=20, choices=Template.choices, default=Template.BASIC
    )
    accent = models.CharField(
        _("color d'accent"), max_length=20, choices=Accent.choices, default=Accent.ACCENT
    )
    menu_order = models.PositiveSmallIntegerField(_("ordre al menú"), default=0)
    in_menu = models.BooleanField(_("al menú"), default=False)
    # Els màxims recomanats (60 i 150) són un avís, no un error (RN-M07-13).
    share_title = models.CharField(_("títol per compartir"), max_length=200, blank=True)
    share_description = models.CharField(_("descripció per compartir"), max_length=500, blank=True)
    status = models.CharField(
        _("estat"), max_length=20, choices=Status.choices, default=Status.DRAFT
    )

    class Meta:
        verbose_name = _("pàgina")
        verbose_name_plural = _("pàgines")
        ordering = ["menu_order", "title"]

    def __str__(self):
        return self.title

    def clean(self):
        if self.slug and route_taken(self.slug):
            raise ValidationError({"slug": _("Aquesta adreça ja és d'una altra pantalla.")})


class PageVersion(AppendOnlyModel):
    """Versió publicada d'una pàgina (RN-M07-03). Només s'hi afegeixen files: l'ORM ho impedeix
    i, a la base de dades, els activadors de la migració 0002."""

    page = models.ForeignKey(
        Page, on_delete=models.PROTECT, related_name="versions", verbose_name=_("pàgina")
    )
    number = models.PositiveIntegerField(_("número"))
    blocks = models.JSONField(_("blocs"), default=list)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name=_("publicada per"),
    )
    published_at = models.DateTimeField(_("publicada el"), auto_now_add=True)
    note = models.CharField(_("nota"), max_length=300, blank=True)

    class Meta:
        verbose_name = _("versió de pàgina")
        verbose_name_plural = _("versions de pàgina")
        ordering = ["page", "number"]
        constraints = [
            models.UniqueConstraint(fields=["page", "number"], name="website_version_unique")
        ]

    def __str__(self):
        return f"{self.page} v{self.number}"


class MediaAsset(models.Model):
    """Foto de la web (M07-6, P-M07-C, RN-M07-05). El contingut és a l'emmagatzematge privat de
    la 00, amb una clau aleatòria; cap carpeta pública (P-489): el serveix una vista declarada
    que ho comprova a cada petició (`media.public_asset`). `key` és el que surt als blocs i a
    l'adreça; l'identificador enter no surt enlloc. Sense fila a `core.PrivateFile` (P-591)."""

    class Status(models.TextChoices):
        ACTIVE = "active", _("Activa")
        RETIRED = "retired", _("Retirada")

    key = models.UUIDField(_("clau pública"), default=uuid.uuid4, unique=True, editable=False)
    storage_key = models.CharField(_("clau a l'emmagatzematge"), max_length=100, unique=True)
    content_type = models.CharField(_("tipus de contingut"), max_length=100)
    size_bytes = models.PositiveBigIntegerField(_("mida (bytes)"))
    alt_text = models.CharField(_("text alternatiu"), max_length=300)
    author = models.CharField(_("autor"), max_length=200, blank=True)
    licence_note = models.CharField(_("permís d'ús"), max_length=300, blank=True)
    shows_people = models.BooleanField(_("s'hi veuen persones"))
    people_consent = models.BooleanField(_("hi ha el consentiment de les persones"), default=False)
    credit = models.CharField(_("crèdit"), max_length=200, blank=True)
    status = models.CharField(
        _("estat"), max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    retired_reason = models.CharField(_("motiu de la retirada"), max_length=300, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+",
        verbose_name=_("pujada per"),
    )  # fmt: skip
    uploaded_at = models.DateTimeField(_("pujada el"), auto_now_add=True)

    class Meta:
        verbose_name = _("foto de la web")
        verbose_name_plural = _("fotos de la web")
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.alt_text

    @property
    def publishable(self) -> bool:
        """RN-M07-05: es pot posar en un bloc publicat."""
        return bool(
            self.status == self.Status.ACTIVE
            and self.alt_text.strip()
            and self.author.strip()
            and self.licence_note.strip()
            and (self.people_consent or not self.shows_people)
        )
