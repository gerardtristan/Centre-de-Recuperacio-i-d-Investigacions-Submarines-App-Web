"""Formulari d'alta: el mateix per a la web (P1) i per a l'alta presencial (P2). T-M01-13.

Dades mínimes de V-04 (RN-M01-02): nom, cognoms, document, correu i telèfon; adreça opcional.
Data de naixement obligatòria i, per a un menor, les dades i l'autorització del pare, la mare o
el tutor legal (068, RN-M01-62 a RN-M01-64). Sense IBAN ni cap dada de salut. El servidor ho
torna a validar tot: el navegador només ajuda.

T-M01-41: per a un menor, el correu i el telèfon del representant són obligatoris i els del menor,
opcionals (Q-011); caselles opcionals i desmarcades del butlletí i de les imatges (Q-031), només
si hi ha text vigent; el passaport, només a l'alta presencial (Q-017).
"""

import re

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.formats import number_format
from django.utils.translation import gettext_lazy as _

from apps.core.models import Person
from apps.core.normalization import normalize_document, normalize_email, normalize_phone

from . import fee_rules
from .models import MembershipType

_DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
_DNI = re.compile(r"^\d{8}[A-Z]$")
_NIE = re.compile(r"^[XYZ]\d{7}[A-Z]$")


_PASSPORT = re.compile(r"^[A-Z0-9]{5,20}$")  # format lliure de cada país [A validar]
PASSPORT = Person.DocumentType.PASSPORT


def parse_document(value: str, *, passport: bool = False) -> tuple[str, str] | None:
    """(tipus, número normalitzat) d'un DNI o NIE amb la lletra correcta, o None. Amb
    `passport`, un número de passaport (només a l'alta presencial, Q-017)."""
    number = normalize_document(value)
    if passport:
        return (PASSPORT, number) if _PASSPORT.match(number) else None
    if _DNI.match(number):
        kind, digits = Person.DocumentType.DNI, number[:8]
    elif _NIE.match(number):
        kind, digits = Person.DocumentType.NIE, str("XYZ".index(number[0])) + number[1:8]
    else:
        return None
    if _DNI_LETTERS[int(digits) % 23] != number[-1]:
        return None
    return kind, number


DOCUMENT_INVALID = _("Escriu un DNI o un NIE vàlid, amb la lletra.")
PASSPORT_INVALID = _("Escriu un número de passaport vàlid, només amb lletres i xifres.")
# Tipus de document: només a l'alta presencial (Q-017). Buit = DNI o NIE.
DOCUMENT_KINDS = [("", _("DNI o NIE")), (PASSPORT, _("Passaport"))]


def clean_phone_value(value: str) -> str:
    """Telèfon normalitzat, de 9 a 15 xifres (alta i edició del soci)."""
    phone = normalize_phone(value)
    if not 9 <= len(phone.lstrip("+")) <= 15:
        raise ValidationError(_("Escriu un telèfon vàlid, de 9 xifres com a mínim."))
    return phone


# Noms dels textos legals de l'alta (els tipus són els de `join.REQUIRED_TEXTS`).
LEGAL_LABELS = {
    "privacy": _("Política de privacitat"),
    "membership_terms": _("Condicions de soci"),
    "guardian_authorization": _("Autorització del pare, la mare o el tutor legal"),
    "newsletter": _("Butlletí del club"),
    "images": _("Ús d'imatges (fotos i vídeos)"),
}
# Textos que accepta tothom, cadascun amb la seva casella; l'autorització, només els menors.
GENERAL_TEXTS = ("privacy", "membership_terms")
GUARDIAN_TEXT = "guardian_authorization"
ACCEPT_FIELDS = {"privacy": "accept_privacy", "membership_terms": "accept_membership_terms"}
# Opcionals (Q-031), separats dels obligatoris; els tipus són els de `join.OPTIONAL_TEXTS`.
OPTIONAL_FIELDS = {"newsletter": "accept_newsletter", "images": "accept_images"}


def _euros(cents: int) -> str:
    return number_format(cents / 100, decimal_pos=2)


class JoinForm(forms.Form):
    """Formulari d'alta. L'edat, el tipus permès i la quota els calcula el servidor amb la data
    local de Barcelona (`fee_rules`); el navegador no envia cap edat ni cap import.

    Estat segons la data de naixement que porta la petició (`self.state`): "unknown" (encara no
    n'hi ha o no és vàlida), "adult", "minor" (14 a 17 anys) o "under14"."""

    first_name = forms.CharField(label=_("Nom"), max_length=100)
    last_name = forms.CharField(label=_("Cognoms"), max_length=150)
    # Obligatori per als majors d'edat i opcional per als menors (068, 09/11/2026): ho decideix
    # el servidor amb la data de naixement, a `clean`. L'etiqueta la fixa `_set_labels`.
    id_document = forms.CharField(max_length=30, required=False)
    # Només a l'alta presencial (Q-017): a la web el camp no existeix i un valor enviat s'ignora.
    id_document_kind = forms.ChoiceField(
        label=_("Tipus de document"), choices=DOCUMENT_KINDS, required=False
    )
    birth_date = forms.DateField(
        label=_("Data de naixement"),
        input_formats=["%Y-%m-%d", "%d/%m/%Y"],
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        error_messages={"invalid": _("Escriu una data vàlida, per exemple 31/12/2010.")},
    )
    # Obligatoris per als majors d'edat i opcionals per als menors (Q-011): ho decideix `clean`.
    contact_email = forms.EmailField(max_length=254, required=False)
    phone = forms.CharField(max_length=30, required=False)
    address = forms.CharField(label=_("Adreça (opcional)"), max_length=255, required=False)
    membership_type = forms.ModelChoiceField(
        label=_("Tipus de soci"),
        queryset=MembershipType.objects.filter(active=True).order_by("annual_fee_cents"),
        empty_label=None,
        widget=forms.RadioSelect(attrs={"class": "visualment-amagat"}),
    )
    # Pare, mare o tutor legal: obligatori només si la persona és menor (RN-M01-62).
    guardian_first_name = forms.CharField(label=_("Nom"), max_length=100, required=False)
    guardian_last_name = forms.CharField(label=_("Cognoms"), max_length=150, required=False)
    guardian_id_document_kind = forms.ChoiceField(
        label=_("Tipus de document"), choices=DOCUMENT_KINDS, required=False
    )
    guardian_id_document = forms.CharField(
        label=_("Document d'identitat (DNI o NIE)"), max_length=30, required=False
    )
    guardian_email = forms.EmailField(label=_("Correu electrònic"), max_length=254, required=False)
    guardian_phone = forms.CharField(label=_("Telèfon"), max_length=30, required=False)
    guardian_authorization = forms.BooleanField(required=False)
    # Un text, una casella, totes obligatòries (09/11/2026). L'autorització del representant
    # (`guardian_authorization`) només ho és per als menors.
    accept_privacy = forms.BooleanField(
        error_messages={
            "required": _("Cal acceptar la política de privacitat per enviar la sol·licitud.")
        }
    )
    accept_membership_terms = forms.BooleanField(
        error_messages={
            "required": _("Cal acceptar les condicions de soci per enviar la sol·licitud.")
        }
    )
    # Opcionals i desmarcats (Q-031): només marcats si la petició els porta marcats. Sense text
    # vigent del tipus, el camp no existeix.
    accept_newsletter = forms.BooleanField(required=False)
    accept_images = forms.BooleanField(required=False)
    # Versions dels textos que s'han mostrat: si n'hi ha una de nova, cal tornar-los a llegir
    # (CA-17.1: es desa la versió exacta acceptada).
    text_versions = forms.CharField(widget=forms.HiddenInput)

    autocomplete = {
        "first_name": "given-name",
        "last_name": "family-name",
        "id_document": "off",
        "birth_date": "bday",
        "contact_email": "email",
        "phone": "tel",
        "address": "street-address",
        "guardian_first_name": "off",
        "guardian_last_name": "off",
        "guardian_id_document": "off",
        "guardian_email": "off",
        "guardian_phone": "off",
    }

    def __init__(self, *args, texts, in_person=False, today=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.texts = texts
        self.in_person = in_person
        self.today = today or fee_rules.local_today()
        if not in_person:
            del self.fields["id_document_kind"], self.fields["guardian_id_document_kind"]
        for kind, name in OPTIONAL_FIELDS.items():
            if kind not in texts:
                del self.fields[name]
        # (tipus, nom, text): el tipus fa d'identificador de la finestra de cada text.
        self.legal = [(kind, LEGAL_LABELS.get(kind, kind), text) for kind, text in texts.items()]
        self.fields["text_versions"].initial = self._versions()
        for name, value in self.autocomplete.items():
            # A l'administració no s'emplena amb les dades de qui fa l'alta.
            self.fields[name].widget.attrs["autocomplete"] = "off" if in_person else value
        for name in ("id_document", "guardian_id_document"):
            self.fields[name].widget.attrs["spellcheck"] = "false"
        self.fields["birth_date"].widget.attrs["max"] = self.today.isoformat()

        self.birth = self._peek_birth_date()
        self.age = fee_rules.age_today(self.birth, self.today) if self.birth else None
        if self.age is None:
            self.state = "unknown"
        elif not fee_rules.is_minor(self.age):
            self.state = "adult"
        elif self.age < fee_rules.FULL_TYPE_MIN_AGE:
            self.state = "under14"
        else:
            self.state = "minor"
        self._set_types()
        self._set_labels()

    # --- Estat que depèn de la data (també per a la vista prèvia del formulari) -------------
    def _peek_birth_date(self):
        """Data de naixement vàlida de la petició, o None. No valida la resta del formulari."""
        if not self.is_bound:
            return None
        field = self.fields["birth_date"]
        try:
            value = field.clean(
                field.widget.value_from_datadict(self.data, self.files, "birth_date")
            )
        except ValidationError:
            return None
        if value > self.today or fee_rules.age_today(value, self.today) > fee_rules.MAX_AGE:
            return None
        return value

    def _set_types(self):
        field = self.fields["membership_type"]
        if self.state == "under14":
            field.queryset = field.queryset.filter(code=fee_rules.SUPPORTER)
        self.fee_note = False
        labels = {t.pk: self._type_label(t) for t in field.queryset}
        field.label_from_instance = lambda obj: labels.get(obj.pk, obj.name)

    def _type_label(self, membership_type) -> str:
        """Quota íntegra i anual (070); per als exempts, fins quan no paguen (068)."""
        name = membership_type.name
        if self.birth is not None:
            preview = fee_rules.fee_preview(
                self.birth, membership_type.annual_fee_cents, self.today
            )
            if preview.kind == "exempt":
                return _("%(name)s · sense quota fins al 31/12/%(year)s") % {
                    "name": name,
                    "year": preview.until_year,
                }
            self.fee_note = True
        return _("%(name)s · quota anual de %(amount)s €") % {
            "name": name,
            "amount": _euros(membership_type.annual_fee_cents),
        }

    def _set_labels(self):
        """Textos de les caselles (qui accepta, segons el canal i l'edat) i de l'edat."""
        minor = self.state in ("minor", "under14")
        if self.in_person:
            self.accept_intro = (
                _(
                    "El pare, la mare o el tutor legal ha llegit i accepta, "
                    "en nom de la persona menor:"
                )
                if minor
                else _("La persona ha llegit i accepta:")
            )
            self.authorization_intro = _(
                "El pare, la mare o el tutor legal autoritza l'alta (pregunta-li-ho):"
            )
        else:
            self.accept_intro = (
                _(
                    "Com a pare, mare o tutor legal, he llegit i accepto, "
                    "en nom de la persona menor:"
                )
                if minor
                else _("He llegit i accepto:")
            )
            self.authorization_intro = _("Com a pare, mare o tutor legal, autoritzo aquesta alta:")
        # Només per als menors (calculat al servidor). Sense JavaScript, el bloc surt quan el
        # servidor torna el formulari amb la data d'un menor i els errors del representant.
        self.show_guardian = minor
        if self.in_person:  # també passaport (Q-017)
            self.fields["guardian_id_document"].label = _("Número de document")
            self.fields["id_document"].label = {
                "unknown": _("Número de document (obligatori per a majors d'edat)"),
                "adult": _("Número de document"),
            }.get(self.state, _("Número de document (opcional)"))
        else:
            self.fields["id_document"].label = {
                "unknown": _("Document d'identitat (DNI o NIE; obligatori per a majors d'edat)"),
                "adult": _("Document d'identitat (DNI o NIE)"),
            }.get(self.state, _("Document d'identitat (DNI o NIE, opcional)"))
        self.fields["contact_email"].label = {
            "unknown": _("Correu electrònic (obligatori per a majors d'edat)"),
            "adult": _("Correu electrònic"),
        }.get(self.state, _("Correu electrònic de la persona menor (opcional)"))
        self.fields["phone"].label = {
            "unknown": _("Telèfon (obligatori per a majors d'edat)"),
            "adult": _("Telèfon"),
        }.get(self.state, _("Telèfon de la persona menor (opcional)"))
        # Qui dona els opcionals: el representant d'un menor de 14 anys (Q-044, opció A); a
        # partir dels 14, el mateix menor (RN-M01-78) [A validar: assessor, Q-016].
        if self.state == "under14":
            self.optional_intro = (
                _(
                    "El pare, la mare o el tutor legal dona el consentiment, en nom de la "
                    "persona menor, per a:"
                )
                if self.in_person
                else _(
                    "Com a pare, mare o tutor legal, dono el consentiment, en nom de la persona "
                    "menor, per a:"
                )
            )
        elif self.state == "minor":
            self.optional_intro = _("La persona menor dona ella mateixa el consentiment per a:")
        else:
            self.optional_intro = (
                _("La persona dona el consentiment per a:")
                if self.in_person
                else _("Dono el meu consentiment per a:")
            )
        self.age_summary = {
            "under14": _(
                "Menor de 14 anys: només pot ser simpatitzant, sense quota, i cal l'autorització "
                "del pare, la mare o el tutor legal."
            ),
            "minor": _("Menor d'edat: cal l'autorització del pare, la mare o el tutor legal."),
        }.get(self.state, "")

    @property
    def general_acceptances(self):
        """(tipus, nom, text, casella) de cada text que accepta tothom."""
        return [
            (kind, label, text, self[ACCEPT_FIELDS[kind]])
            for kind, label, text in self.legal
            if kind in GENERAL_TEXTS
        ]

    @property
    def optional_acceptances(self):
        """(tipus, nom, text, casella) de cada consentiment opcional amb text vigent."""
        return [
            (kind, label, text, self[OPTIONAL_FIELDS[kind]])
            for kind, label, text in self.legal
            if kind in OPTIONAL_FIELDS
        ]

    @property
    def guardian_acceptance(self):
        return [
            (kind, label, text, self["guardian_authorization"])
            for kind, label, text in self.legal
            if kind == GUARDIAN_TEXT
        ]

    # --- Validació ---------------------------------------------------------------------------
    def _versions(self) -> str:
        return ";".join(f"{kind}:{text.version}" for kind, text in self.texts.items())

    def _passport(self, name) -> bool:
        """S'ha triat el passaport. El camp només existeix a l'alta presencial (Q-017): a la web
        sempre és DNI o NIE, encara que la petició digui una altra cosa."""
        if name not in self.fields:
            return False
        widget = self.fields[name].widget
        return widget.value_from_datadict(self.data, self.files, self.add_prefix(name)) == PASSPORT

    def _parse(self, raw, kind_field):
        """(tipus, número), o ValidationError amb el missatge del tipus triat."""
        passport = self._passport(kind_field)
        parsed = parse_document(raw, passport=passport)
        if parsed is None:
            raise ValidationError(PASSPORT_INVALID if passport else DOCUMENT_INVALID)
        return parsed

    def clean_id_document(self):
        """(tipus, número) si s'ha escrit, validat amb la lletra; None si és buit. Que sigui
        obligatori (adults) es decideix a `clean`, amb l'edat."""
        raw = self.cleaned_data["id_document"].strip()
        return self._parse(raw, "id_document_kind") if raw else None

    def clean_birth_date(self):
        value = self.cleaned_data["birth_date"]
        if value > self.today:
            raise ValidationError(_("La data de naixement no pot ser posterior a avui."))
        if fee_rules.age_today(value, self.today) > fee_rules.MAX_AGE:
            raise ValidationError(_("Revisa la data de naixement."))
        return value

    def clean_phone(self):
        # Buit: el decideix `clean` amb l'edat (opcional per als menors, Q-011).
        value = self.cleaned_data["phone"]
        return clean_phone_value(value) if value.strip() else ""

    def clean_text_versions(self):
        if self.cleaned_data["text_versions"] != self._versions():
            raise ValidationError(
                _(
                    "Els textos legals han canviat mentre omplies el formulari. Llegeix-los de "
                    "nou i torna a enviar la sol·licitud."
                )
            )
        return self.cleaned_data["text_versions"]

    def clean(self):
        cleaned = super().clean()
        if "id_document" in cleaned:
            cleaned["id_document_type"], cleaned["id_document_number"] = cleaned["id_document"] or (
                "",
                "",
            )
        birth = cleaned.get("birth_date")
        if birth is None:
            return cleaned
        age = fee_rules.age_today(birth, self.today)
        cleaned["on"] = self.today
        adult = not fee_rules.is_minor(age)
        if "id_document" in cleaned and adult and not cleaned["id_document"]:
            self.add_error("id_document", self.fields["id_document"].error_messages["required"])
        for name in ("contact_email", "phone"):
            if name in cleaned and adult and not cleaned[name]:
                self.add_error(name, self.fields[name].error_messages["required"])
        if self.state == "under14" and "membership_type" in self.errors:
            # El ple dret no és a les opcions: un formulari manipulat rep aquest missatge.
            self.errors["membership_type"] = self.error_class([UNDER14_TYPE])
        chosen = cleaned.get("membership_type")
        if chosen is not None and not fee_rules.may_choose(chosen.code, age):
            self.add_error("membership_type", UNDER14_TYPE)
        cleaned["minor"] = fee_rules.is_minor(age)
        if cleaned["minor"]:
            self._clean_guardian(cleaned)
        else:
            # Minimització: d'un adult no es desa cap dada de representant.
            for name in ("guardian_first_name", "guardian_last_name", "guardian_email"):
                cleaned[name] = ""
            cleaned["guardian_phone"] = ""
            cleaned["guardian_id_document_type"] = cleaned["guardian_id_document_number"] = ""
            cleaned["guardian_authorization"] = False
        return cleaned

    def _clean_guardian(self, cleaned):
        required = _("Per a una persona menor, és obligatori.")
        for name in ("guardian_first_name", "guardian_last_name"):
            cleaned[name] = (cleaned.get(name) or "").strip()
            if not cleaned[name]:
                self.add_error(name, required)
        raw = (cleaned.get("guardian_id_document") or "").strip()
        parsed = None
        if not raw:
            self.add_error("guardian_id_document", required)
        else:
            try:
                parsed = self._parse(raw, "guardian_id_document_kind")
            except ValidationError as error:
                self.add_error("guardian_id_document", error)
        if parsed and parsed[1] == cleaned.get("id_document_number"):
            self.add_error("guardian_id_document", GUARDIAN_OWN_DOCUMENT)
        if parsed:
            cleaned["guardian_id_document_type"], cleaned["guardian_id_document_number"] = parsed
        # Q-011 (opció 3): el correu i el telèfon del representant, obligatoris.
        cleaned["guardian_email"] = normalize_email(cleaned.get("guardian_email"))
        if not cleaned["guardian_email"] and "guardian_email" not in self.errors:
            self.add_error("guardian_email", required)
        raw_phone = (cleaned.get("guardian_phone") or "").strip()
        try:
            cleaned["guardian_phone"] = clean_phone_value(raw_phone) if raw_phone else ""
        except ValidationError as error:
            self.add_error("guardian_phone", error)
        else:
            if not raw_phone:
                self.add_error("guardian_phone", required)
        if not cleaned.get("guardian_authorization"):
            self.add_error("guardian_authorization", GUARDIAN_AUTHORIZATION_REQUIRED)


UNDER14_TYPE = _("Amb menys de 14 anys només es pot ser simpatitzant.")
GUARDIAN_OWN_DOCUMENT = _(
    "El document del pare, la mare o el tutor legal ha de ser el seu, no el de la persona menor."
)
GUARDIAN_AUTHORIZATION_REQUIRED = _(
    "Sense l'autorització del pare, la mare o el tutor legal, no es pot enviar l'alta."
)


class ProfileForm(forms.Form):
    """El meu perfil (T-M01-16; HU-M01-08): telèfon i adreça. El selector de llengua només hi és
    si hi ha més d'una llengua activa, i només n'admet de les actives (061). Qualsevol altre camp
    que porti la petició (nom, document, correu) s'ignora: no és al formulari."""

    phone = forms.CharField(
        label=_("Telèfon"), max_length=30, widget=forms.TextInput(attrs={"autocomplete": "tel"})
    )
    address = forms.CharField(
        label=_("Adreça (opcional)"),
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "street-address"}),
    )
    # Camps opcionals (P-58, 072): mai obligatoris per ser soci.
    landline = forms.CharField(
        label=_("Telèfon fix (opcional)"),
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "tel"}),
    )
    postal_code = forms.CharField(
        label=_("Codi postal (opcional)"),
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "postal-code"}),
    )
    city = forms.CharField(
        label=_("Població (opcional)"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "address-level2"}),
    )
    province = forms.CharField(
        label=_("Província (opcional)"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "address-level1"}),
    )
    preferred_language = forms.ChoiceField(label=_("Llengua"))

    clean_phone = JoinForm.clean_phone  # la mateixa regla que a l'alta (V-04)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if len(settings.LANGUAGES) > 1:
            self.fields["preferred_language"].choices = settings.LANGUAGES
        else:
            del self.fields["preferred_language"]
