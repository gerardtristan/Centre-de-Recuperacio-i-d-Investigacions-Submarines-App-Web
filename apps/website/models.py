"""Models del 07 (M07-6). Cap camp guarda HTML: el text es desa tal qual i s'escapa en mostrar-lo
(RN-M07-10). Les llistes de plantilles, d'accents i de tipus de bloc són codi (M07-6, «Es queden
al codi»)."""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import AppendOnlyModel

from .routes import route_exists, route_taken


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


class PageDraft(models.Model):
    """L'únic esborrany d'una pàgina (RN-M07-16, decisió 106). Es reescriu a cada desat; el que
    no es pot canviar són les versions publicades (`PageVersion`)."""

    page = models.OneToOneField(
        Page, on_delete=models.PROTECT, related_name="draft", verbose_name=_("pàgina")
    )
    blocks = models.JSONField(_("blocs"), default=list)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+",
        verbose_name=_("desat per"),
    )  # fmt: skip
    updated_at = models.DateTimeField(_("desat el"), auto_now=True)

    class Meta:
        verbose_name = _("esborrany de pàgina")
        verbose_name_plural = _("esborranys de pàgina")

    def __str__(self):
        return str(self.page)


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


class ContactReason(models.Model):
    """Motiu de contacte (M07-6; RN-M07-07). És una dada (WP8): el nom, si surt al formulari i
    els rols que reben els seus missatges, que fan l'abast per motiu de WP5. D'inici, tots a la
    Secretaria (P-486, provisional)."""

    name = models.CharField(_("nom"), max_length=100, unique=True)
    active = models.BooleanField(_("actiu"), default=True)
    order = models.PositiveSmallIntegerField(_("ordre"), default=0)
    roles = models.ManyToManyField(
        "core.Role", blank=True, related_name="+", verbose_name=_("rols que el reben")
    )

    class Meta:
        verbose_name = _("motiu de contacte")
        verbose_name_plural = _("motius de contacte")
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class ContactMessage(models.Model):
    """Missatge del formulari de contacte (M07-6). Sense IP (M07-12). `finished_at` és quan es
    respon o es tanca: d'allà compta la conservació (RN-M07-07, P-620)."""

    class Status(models.TextChoices):
        NEW = "new", _("Nou")
        ANSWERED = "answered", _("Respost")
        CLOSED = "closed", _("Tancat")

    reason = models.ForeignKey(
        ContactReason, on_delete=models.PROTECT, related_name="messages", verbose_name=_("motiu")
    )
    name = models.CharField(_("nom"), max_length=150)
    email = models.EmailField(_("correu electrònic"), max_length=254)
    body = models.TextField(_("missatge"), max_length=5000)
    privacy_text = models.ForeignKey(
        "core.LegalText", on_delete=models.PROTECT, related_name="+",
        verbose_name=_("text de privacitat acceptat"),
    )  # fmt: skip
    status = models.CharField(_("estat"), max_length=20, choices=Status.choices, default=Status.NEW)
    answered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="+", verbose_name=_("respost per"),
    )  # fmt: skip
    answer = models.TextField(_("resposta"), blank=True)
    closed_reason = models.CharField(_("motiu del tancament"), max_length=300, blank=True)
    created_at = models.DateTimeField(_("rebut el"), auto_now_add=True)
    finished_at = models.DateTimeField(_("respost o tancat el"), null=True, blank=True)

    class Meta:
        verbose_name = _("missatge de contacte")
        verbose_name_plural = _("missatges de contacte")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reason} · {self.created_at:%d/%m/%Y}"


class NewsletterSubscription(models.Model):
    """Subscripció al butlletí (M07-6; RN-M07-06 i 08; P-492: fila pròpia del 07, no una persona
    de la 00). Només el correu i la versió del text acceptada (M07-12). `token` és l'enllaç de
    confirmació i de baixa: es renova en cada petició nova i no surt mai al registre."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Pendent de confirmar")
        CONFIRMED = "confirmed", _("Confirmada")
        UNSUBSCRIBED = "unsubscribed", _("De baixa")

    email = models.EmailField(_("correu electrònic"), max_length=254, unique=True)
    status = models.CharField(
        _("estat"), max_length=20, choices=Status.choices, default=Status.PENDING
    )
    legal_text = models.ForeignKey(
        "core.LegalText", on_delete=models.PROTECT, related_name="+",
        verbose_name=_("text del butlletí acceptat"),
    )  # fmt: skip
    token = models.CharField(_("enllaç"), max_length=64, unique=True)
    requested_at = models.DateTimeField(_("demanada el"))
    confirmed_at = models.DateTimeField(_("confirmada el"), null=True, blank=True)
    unsubscribed_at = models.DateTimeField(_("de baixa el"), null=True, blank=True)

    class Meta:
        verbose_name = _("subscripció al butlletí")
        verbose_name_plural = _("subscripcions al butlletí")

    def __str__(self):
        return self.get_status_display()


class NewsletterEvent(AppendOnlyModel):
    """Esdeveniments d'una subscripció (M07-6): només s'hi afegeixen files."""

    class Kind(models.TextChoices):
        REQUESTED = "requested", _("Demanada")
        CONFIRMED = "confirmed", _("Confirmada")
        UNSUBSCRIBED = "unsubscribed", _("Baixa")

    subscription = models.ForeignKey(
        NewsletterSubscription, on_delete=models.PROTECT, related_name="events",
        verbose_name=_("subscripció"),
    )  # fmt: skip
    kind = models.CharField(_("tipus"), max_length=20, choices=Kind.choices)
    legal_text = models.ForeignKey(
        "core.LegalText", on_delete=models.PROTECT, null=True, blank=True, related_name="+",
        verbose_name=_("text acceptat"),
    )  # fmt: skip
    at = models.DateTimeField(_("data"), auto_now_add=True)

    class Meta:
        verbose_name = _("esdeveniment del butlletí")
        verbose_name_plural = _("esdeveniments del butlletí")
        ordering = ["subscription", "at", "pk"]


class Newsletter(models.Model):
    """Butlletí (M07-6; P-M07-F, RN-M07-06). Text pla (RN-M07-10). D'esborrany a enviat una sola
    vegada; enviat, ja no es canvia. Els recomptes surten dels enviaments (`newsletter.counts`)."""

    class Status(models.TextChoices):
        DRAFT = "draft", _("Esborrany")
        SENT = "sent", _("Enviat")

    number = models.PositiveIntegerField(_("número"), unique=True)
    subject = models.CharField(_("assumpte"), max_length=200)
    body = models.TextField(_("cos"), max_length=20000)
    status = models.CharField(
        _("estat"), max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+",
        verbose_name=_("redactat per"),
    )  # fmt: skip
    created_at = models.DateTimeField(_("redactat el"), auto_now_add=True)
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="+", verbose_name=_("enviat per"),
    )  # fmt: skip
    sent_at = models.DateTimeField(_("enviat el"), null=True, blank=True)

    class Meta:
        verbose_name = _("butlletí")
        verbose_name_plural = _("butlletins")
        ordering = ["-number"]

    def __str__(self):
        return f"{self.number} · {self.subject}"


class NewsletterDelivery(models.Model):
    """Un enviament d'un butlletí a una subscripció confirmada (CA-M07-08). Una sola fila per
    subscripció i butlletí: el mateix butlletí no arriba dues vegades."""

    newsletter = models.ForeignKey(
        Newsletter, on_delete=models.PROTECT, related_name="deliveries", verbose_name=_("butlletí")
    )
    subscription = models.ForeignKey(
        NewsletterSubscription, on_delete=models.PROTECT, related_name="deliveries",
        verbose_name=_("subscripció"),
    )  # fmt: skip
    email = models.ForeignKey(
        "core.OutgoingEmail", on_delete=models.PROTECT, null=True, blank=True, related_name="+",
        verbose_name=_("correu"),
    )  # fmt: skip
    # Es dona de baixa abans que surti el seu lot: no se li envia (RN-M07-06).
    skipped = models.BooleanField(_("no enviat per baixa"), default=False)

    class Meta:
        verbose_name = _("enviament del butlletí")
        verbose_name_plural = _("enviaments del butlletí")
        constraints = [
            models.UniqueConstraint(
                fields=["newsletter", "subscription"], name="website_delivery_unique"
            )
        ]

    def __str__(self):
        return f"{self.newsletter} · {self.pk}"


class NewsItem(models.Model):
    """Notícia (M07-6, P-M07-B). Només es veu publicada (RN-M07-02); retirar-la demana motiu."""

    class Status(models.TextChoices):
        DRAFT = "draft", _("Esborrany")
        PUBLISHED = "published", _("Publicada")
        RETIRED = "retired", _("Retirada")

    title = models.CharField(_("títol"), max_length=200)
    slug = models.SlugField(_("adreça"), max_length=80, unique=True)
    date = models.DateField(_("data"))
    body = models.TextField(_("cos"))
    image = models.ForeignKey(
        MediaAsset, on_delete=models.PROTECT, null=True, blank=True, related_name="+",
        verbose_name=_("foto"),
    )  # fmt: skip
    status = models.CharField(
        _("estat"), max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    retired_reason = models.CharField(_("motiu de la retirada"), max_length=300, blank=True)

    class Meta:
        verbose_name = _("notícia")
        verbose_name_plural = _("notícies")
        ordering = ["-date", "-pk"]

    def __str__(self):
        return self.title


class FaqTopic(models.Model):
    """Tema de les preguntes freqüents (M07-6, M07b)."""

    name = models.CharField(_("nom"), max_length=100, unique=True)
    order = models.PositiveSmallIntegerField(_("ordre"), default=0)

    class Meta:
        verbose_name = _("tema de l'ajuda")
        verbose_name_plural = _("temes de l'ajuda")
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class FaqEntry(models.Model):
    """Pregunta freqüent (M07-6). Només es veu publicada; el text s'escapa en mostrar-lo."""

    topic = models.ForeignKey(
        FaqTopic, on_delete=models.PROTECT, related_name="entries", verbose_name=_("tema")
    )
    question = models.CharField(_("pregunta"), max_length=300)
    answer = models.TextField(_("resposta"))
    order = models.PositiveSmallIntegerField(_("ordre"), default=0)
    published = models.BooleanField(_("publicada"), default=False)

    class Meta:
        verbose_name = _("pregunta freqüent")
        verbose_name_plural = _("preguntes freqüents")
        ordering = ["topic__order", "topic__name", "order", "pk"]

    def __str__(self):
        return self.question


class Tutorial(models.Model):
    """Tutorial de l'ajuda (M07-6; RN-M07-10 i 11): els passos escrits en text pla, una foto
    opcional de la web (amb la regla RN-M07-05) i la pantalla on surt «Mira com es fa»
    (`screen_code`, el nom de la ruta: p. ex. `payments:charge`). El vídeo espera la decisió 106."""

    title = models.CharField(_("títol"), max_length=200)
    slug = models.SlugField(_("adreça"), max_length=80, unique=True)
    steps = models.TextField(_("passos"), max_length=10000)
    image = models.ForeignKey(
        MediaAsset, on_delete=models.PROTECT, null=True, blank=True, related_name="+",
        verbose_name=_("foto"),
    )  # fmt: skip
    screen_code = models.CharField(_("pantalla"), max_length=100, blank=True)
    order = models.PositiveSmallIntegerField(_("ordre"), default=0)
    published = models.BooleanField(_("publicat"), default=False)

    class Meta:
        verbose_name = _("tutorial")
        verbose_name_plural = _("tutorials")
        ordering = ["order", "title"]

    def __str__(self):
        return self.title

    def clean(self):
        if self.screen_code and not route_exists(self.screen_code):
            raise ValidationError({"screen_code": _("Aquesta pantalla no existeix.")})

    @property
    def step_list(self) -> list[str]:
        """Un pas per línia, sense les línies buides."""
        return [line.strip() for line in self.steps.splitlines() if line.strip()]
