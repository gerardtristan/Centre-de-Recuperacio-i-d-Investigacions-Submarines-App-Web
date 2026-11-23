"""Formularis de l'administració del 02 (T-M02-06). Només recullen les dades (imports en euros,
desats en cèntims); els serveis tornen a comprovar totes les regles. Els desplegables només
ofereixen el que es pot triar, mai tot el cens."""

import re

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.charges import euros
from apps.core.models import Department, Person
from apps.core.permissions import accounts_with_perm

from . import catalogue, extensions, permissions
from .models import (
    Activity,
    CertificationLevel,
    EnvironmentalProject,
    EnvironmentalSubtype,
    OutingType,
    Place,
    RequirementsMode,
    SpecialitiesRule,
    TrainingCatalogueEntry,
)

DATE_ERROR = _("Escriu una data vàlida, per exemple 14/06/2027.")
MOMENT_ERROR = _("Escriu el dia i l'hora, per exemple 14/06/2027 09:00.")
_EUROS = re.compile(r"^(\d{1,6})(?:[.,](\d{1,2}))?$")


class EuroField(forms.Field):
    """Un import en euros que es desa en cèntims (enter). «45», «45,5» i «45.50» valen."""

    widget = forms.TextInput
    default_error_messages = {"invalid": _("Escriu l'import en euros, per exemple 45 o 45,50.")}

    def __init__(self, **kwargs):
        kwargs.setdefault("help_text", _("En euros. Zero vol dir gratuït."))
        super().__init__(**kwargs)
        self.widget.attrs.update({"inputmode": "decimal", "autocomplete": "off", "maxlength": 12})

    def to_python(self, value):
        text = str(value or "").replace("€", "").replace(" ", "").strip()
        if not text:
            return None
        match = _EUROS.match(text)
        if not match:
            raise forms.ValidationError(self.error_messages["invalid"], code="invalid")
        return int(match.group(1)) * 100 + int((match.group(2) or "0").ljust(2, "0"))

    def prepare_value(self, value):
        if isinstance(value, int) and not isinstance(value, bool):
            return f"{value // 100},{value % 100:02d}"
        return value


def date_field(label, **kwargs):
    return forms.DateField(
        label=label,
        input_formats=["%Y-%m-%d", "%d/%m/%Y"],
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        error_messages={"invalid": DATE_ERROR},
        **kwargs,
    )


def moment_field(label, **kwargs):
    return forms.DateTimeField(
        label=label,
        input_formats=["%Y-%m-%dT%H:%M", "%d/%m/%Y %H:%M"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        error_messages={"invalid": MOMENT_ERROR},
        **kwargs,
    )


def _text(rows=4):
    return forms.Textarea(attrs={"rows": rows})


class _Named(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class _EntryChoice(forms.ModelChoiceField):
    def label_from_instance(self, entry):
        return f"{entry.get_kind_display()}: {entry.name}"


class _PlaceChoice(forms.ModelChoiceField):
    """El lloc i el seu preu estàndard d'avui: amb AC7 es veu, també sense AC21 (RN-M02-46)."""

    def label_from_instance(self, place):
        price = catalogue.place_price_on(place, timezone.localdate())
        if price is None:
            return place.name
        return _("%(place)s (estàndard: %(member)s soci, %(non_member)s no soci)") % {
            "place": place.name,
            "member": euros(price.price_member_cents),
            "non_member": euros(price.price_non_member_cents),
        }


def responsible_people():
    """Qui pot ser responsable: només les persones amb un compte amb AC7, mai tot el cens."""
    accounts = accounts_with_perm(permissions.MANAGE, write=True)
    return Person.objects.filter(
        pk__in=[account.person_id for account in accounts], status=Person.Status.ACTIVE
    ).order_by("first_name", "last_name", "pk")


def _keep(queryset, model, pk):
    """El que l'activitat ja té triat s'hi manté encara que ara estigui desactivat."""
    return (queryset | model.objects.filter(pk=pk)).distinct() if pk else queryset


class ActivityForm(forms.Form):
    """Crear o editar un curs o una sortida. En una activitat nova, les places i els preus es
    poden deixar en blanc: es copien de la fitxa del catàleg (curs) o del lloc (sortida)."""

    catalogue_entry = _EntryChoice(
        label=_("Fitxa del catàleg"),
        queryset=TrainingCatalogueEntry.objects.none(),
        help_text=_("Se'n copien les places, els preus vigents avui i el departament."),
    )
    outing_type = forms.ModelChoiceField(
        label=_("Tipus de sortida"), queryset=OutingType.objects.none()
    )
    subtype = forms.ModelChoiceField(
        label=_("Subtipus"), queryset=EnvironmentalSubtype.objects.none(), required=False,
        help_text=_("Només per a les sortides de medi ambient, que n'han de tenir."),
    )  # fmt: skip
    project = forms.ModelChoiceField(
        label=_("Projecte"), queryset=EnvironmentalProject.objects.none(), required=False,
        help_text=_("Només per a les sortides de medi ambient. És opcional."),
    )  # fmt: skip
    title = forms.CharField(label=_("Títol"), max_length=140)
    description = forms.CharField(label=_("Descripció o objectiu"), required=False, widget=_text())
    starts_on = date_field(_("Data d'inici"))
    ends_on = date_field(_("Data de final"))
    place = _PlaceChoice(label=_("Lloc"), queryset=Place.objects.none(), required=False)
    meeting_point = forms.CharField(label=_("Punt de trobada"), max_length=140, required=False)
    registration_closes_at = moment_field(
        _("Data límit d'inscripció"), help_text=_("Com a molt tard, el dia d'inici.")
    )
    max_places = forms.IntegerField(label=_("Places"), min_value=1, max_value=500)
    price_member_cents = EuroField(label=_("Preu de soci"))
    price_non_member_cents = EuroField(label=_("Preu de no soci"))
    price_override_note = forms.CharField(
        label=_("Motiu del preu diferent de l'estàndard"), required=False, widget=_text(2),
        help_text=_("Obligatori si algun preu no és l'estàndard (del catàleg o del lloc)."),
    )  # fmt: skip
    payment_window_hours = forms.IntegerField(
        label=_("Termini de pagament (hores)"), min_value=1, max_value=720, required=False
    )
    open_to_non_members = forms.BooleanField(label=_("Oberta a no socis"), required=False)
    required_level = forms.CharField(
        label=_("Titulació mínima (text)"), max_length=60, required=False,
        help_text=_("Només informatiu. El que es comprova és el nivell mínim."),
    )  # fmt: skip
    min_level = forms.ModelChoiceField(
        label=_("Nivell mínim"), queryset=CertificationLevel.objects.none(), required=False,
        help_text=_("Compleix qui té aquest nivell o un de més alt."),
    )  # fmt: skip
    required_specialities = _Named(
        label=_("Especialitats exigides"), queryset=TrainingCatalogueEntry.objects.none(),
        required=False, widget=forms.CheckboxSelectMultiple,
    )  # fmt: skip
    specialities_rule = forms.ChoiceField(
        label=_("Quantes especialitats calen"),
        choices=SpecialitiesRule.choices,
        required=False,
    )
    min_age = forms.IntegerField(
        label=_("Edat mínima"), min_value=1, max_value=99, required=False,
        help_text=_("En anys. En blanc, sense edat mínima."),
    )  # fmt: skip
    licence_required = forms.BooleanField(label=_("Cal llicència vigent"), required=False)
    requirements_mode = forms.ChoiceField(
        label=_("Si algú no compleix els requisits"),
        choices=RequirementsMode.choices,
        required=False,
    )
    responsible = forms.ModelChoiceField(
        label=_("Persona responsable"), queryset=Person.objects.none()
    )
    department = forms.ModelChoiceField(
        label=_("Departament"), queryset=Department.objects.none(), required=False
    )
    forecast_url = forms.CharField(
        label=_("Enllaç a la previsió marítima"), max_length=200, required=False,
        help_text=_("Una adreça que comenci per https://. Només s'hi posa l'enllaç."),
    )  # fmt: skip

    COURSE_ONLY = ("catalogue_entry",)
    OUTING_ONLY = ("outing_type", "subtype", "project")
    COPIED = ("max_places", "price_member_cents", "price_non_member_cents")
    OPTIONAL_DEFAULTS = ("payment_window_hours", "requirements_mode", "department")

    def __init__(self, data=None, *, kind, activity=None, user=None):
        self.kind, self.activity = kind, activity
        course = kind == Activity.Kind.COURSE
        initial = {}
        if activity is not None:
            initial = {n: getattr(activity, n) for n in self.base_fields if hasattr(activity, n)}
            initial["required_specialities"] = list(
                activity.required_specialities.values_list("pk", flat=True)
            )
        elif user is not None:
            initial = {"responsible": user.person_id}
        super().__init__(data, initial=initial)
        for name in self.OUTING_ONLY if course else self.COURSE_ONLY:
            del self.fields[name]
        keep = activity.responsible_id if activity else None
        self.fields["responsible"].queryset = _keep(responsible_people(), Person, keep)
        self.fields["department"].queryset = Department.objects.filter(active=True)
        place = self.fields["place"]
        place.queryset = _keep(
            Place.objects.filter(active=True), Place, activity and activity.place_id
        )
        place.required = not course
        if course:
            place.help_text = _("Opcional: el lloc de cada classe va a la sessió.")
        levels = CertificationLevel.objects.filter(active=True)
        self.fields["min_level"].queryset = _keep(
            levels, CertificationLevel, activity and activity.min_level_id
        ).order_by("rank")
        specialities = TrainingCatalogueEntry.objects.filter(
            kind=TrainingCatalogueEntry.Kind.SPECIALITY, active=True
        )
        if activity is not None:
            specialities = specialities | activity.required_specialities.all()
        self.fields["required_specialities"].queryset = specialities.distinct().order_by("name")
        if activity is None:
            for name in (*self.COPIED, *self.OPTIONAL_DEFAULTS, "specialities_rule"):
                self.fields[name].required = False
            source = _("de la fitxa del catàleg") if course else _("del preu estàndard del lloc")
            for name in self.COPIED:
                self.fields[name].help_text = _("En blanc, es copia %(source)s.") % {
                    "source": source
                }
            if course:
                self.fields["catalogue_entry"].queryset = TrainingCatalogueEntry.objects.filter(
                    active=True
                ).order_by("kind", "name")
            else:
                self.fields["max_places"].required = True
                self.fields["max_places"].help_text = ""
        elif course:
            del self.fields["catalogue_entry"]  # la fitxa no es canvia mai
        if not course:
            self.fields["outing_type"].queryset = _keep(
                OutingType.objects.filter(active=True),
                OutingType,
                activity and activity.outing_type_id,
            )
            self.fields["subtype"].queryset = _keep(
                EnvironmentalSubtype.objects.filter(active=True), EnvironmentalSubtype,
                activity and activity.subtype_id,
            )  # fmt: skip
            self.fields["project"].queryset = _keep(
                EnvironmentalProject.objects.filter(status=EnvironmentalProject.Status.ACTIVE),
                EnvironmentalProject, activity and activity.project_id,
            )  # fmt: skip

    def clean(self):
        data = super().clean()
        place = data.get("place")
        blank = data.get("price_member_cents") is None or data.get("price_non_member_cents") is None
        if (
            self.activity is None
            and self.kind == Activity.Kind.OUTING
            and place is not None
            and blank
            and catalogue.place_price_on(place, timezone.localdate()) is None
        ):
            self.add_error(
                "price_member_cents", _("Aquest lloc no té preu estàndard: escriu els dos preus.")
            )
        return data

    def service_data(self) -> dict:
        """Les dades tal com les esperen `services.create_*` i `services.update_activity`: el
        que s'ha deixat en blanc perquè es copiï o prengui el valor per defecte no s'hi posa."""
        data = dict(self.cleaned_data)
        if self.activity is None:
            blank = [*self.COPIED, *self.OPTIONAL_DEFAULTS, "specialities_rule", "place"]
            if self.kind == Activity.Kind.COURSE:
                blank.append("min_age")  # en blanc, la de la fitxa del catàleg
            for name in blank:
                if name in data and data[name] in (None, ""):
                    del data[name]
        elif data.get("specialities_rule") in (None, ""):
            del data["specialities_rule"]
        data["required_specialities"] = list(data.get("required_specialities") or ())
        return data


class MaterialCostForm(forms.Form):
    """Cost de material previst per participant (RN-M02-43; AC23): una previsió, sense càrrec."""

    cost = EuroField(label=_("Cost de material previst per participant"), help_text="")
    note = forms.CharField(
        label=_("Motiu si no és l'estàndard"), required=False, widget=_text(2),
        help_text=_("Obligatori si el cost no és el que calcula el 03."),
    )  # fmt: skip


class GuestEnrolmentForm(forms.Form):
    """Inscripció d'un convidat (T-M02-14; RN-M02-35; CA-M02-10, 11 i 37): dades mínimes, i la
    data de naixement només si l'activitat té edat mínima; si no, la casella «Soc major d'edat»
    (T-M02-34). Les regles i els textos legals vigents els comprova `guests.enrol_guest`."""

    first_name = forms.CharField(label=_("Nom"), max_length=100)
    last_name = forms.CharField(label=_("Cognoms"), max_length=150)
    contact_email = forms.EmailField(label=_("Correu electrònic"), max_length=254)
    phone = forms.CharField(label=_("Telèfon (opcional)"), max_length=30, required=False)
    birth_date = date_field(_("Data de naixement"))
    adult_declared = forms.BooleanField(
        label=_("Declaració «Soc major d'edat»"), required=False,
        error_messages={"required": _("Cal confirmar que ets major d'edat.")},
    )  # fmt: skip
    accept_privacy = forms.BooleanField(
        label=_("Política de privacitat"), required=False,
        error_messages={"required": _("Cal acceptar la política de privacitat.")},
    )  # fmt: skip

    def __init__(self, data=None, *, min_age, prefix=None):
        super().__init__(data, prefix=prefix)
        if min_age:
            del self.fields["adult_declared"]
        else:
            del self.fields["birth_date"]
        for name in ("adult_declared", "accept_privacy"):
            if name in self.fields:
                self.fields[name].required = True


class PlaceForm(forms.Form):
    """Nom i notes d'un lloc (RN-M02-38), amb els camps que hi afegeixen altres mòduls
    (`extensions.register_place_section`; el 03, el centre habitual)."""

    name = forms.CharField(label=_("Nom"), max_length=120)
    notes = forms.CharField(
        label=_("Notes internes"), max_length=1000, required=False, widget=_text(3),
        help_text=_("Sense dades personals ni de salut. No surten mai al públic."),
    )  # fmt: skip

    def __init__(self, data=None, *, viewer, place=None):
        initial = {"name": place.name, "notes": place.notes} if place else None
        super().__init__(data, initial=initial)
        self.sections = []
        for section in extensions.place_sections():
            names = {}
            for name, field in section.fields(place, viewer).items():
                key = f"{section.key.replace('.', '_')}__{name}"
                self.fields[key], names[key] = field, name
            if names:
                self.sections.append((section, names))

    def save_sections(self, place, by) -> None:
        for section, names in self.sections:
            section.save(place, {name: self.cleaned_data[key] for key, name in names.items()}, by)


class PlacePriceForm(forms.Form):
    """Un preu estàndard nou del lloc, vigent des d'avui o més endavant, amb motiu (RN-M02-39)."""

    price_member_cents = EuroField(label=_("Preu de soci"))
    price_non_member_cents = EuroField(label=_("Preu de no soci"))
    valid_from = date_field(_("Vigent des del"), help_text=_("Avui o més endavant."))
    note = forms.CharField(label=_("Motiu del canvi"), widget=_text(2))


class CataloguePriceForm(PlacePriceForm):
    """Una versió nova dels preus d'una fitxa del catàleg, amb data i motiu (RN-M02-05)."""

    reinforcement_price_cents = EuroField(label=_("Preu d'una classe de reforç"), required=False)
    field_order = catalogue.PRICE_FIELDS


class EntryForm(forms.ModelForm):
    """Fitxa del catàleg: nova (amb el catàleg i els preus inicials) o les dades que no són preus.
    Els serveis (`catalogue.create_entry` i `update_entry`) ho tornen a comprovar."""

    price_member_cents = EuroField(label=_("Preu de soci"))
    price_non_member_cents = EuroField(label=_("Preu de no soci"))
    reinforcement_price_cents = EuroField(label=_("Preu d'una classe de reforç"), required=False)
    NEW_ONLY = ("kind", *catalogue.PRICE_FIELDS)

    class Meta:
        model = TrainingCatalogueEntry
        fields = ("kind", "name", *catalogue.PRICE_FIELDS, *catalogue.EDITABLE_FIELDS[1:])
        widgets = {"description": _text(), "requirements": _text(3)}

    def __init__(self, data=None, *, entry=None):
        super().__init__(data, instance=entry)
        if entry is not None:
            for name in self.NEW_ONLY:
                del self.fields[name]
        self.fields["department"].queryset = _keep(
            Department.objects.filter(active=True), Department, entry and entry.department_id
        )

    def _post_clean(self):
        pass  # sense validar ni tocar el model: les regles són als serveis


class OutingTypeForm(forms.ModelForm):
    """Tipus de sortida nou (AC6). El servei `catalogue.create_outing_type` ho torna a comprovar."""

    class Meta:
        model = OutingType
        fields = ("name", "default_department", "is_environmental", "default_requirements_mode")

    def __init__(self, data=None):
        super().__init__(data, prefix="tipus")
        self.fields["default_department"].queryset = Department.objects.filter(active=True)


class SubtypeForm(forms.ModelForm):
    class Meta:
        model = EnvironmentalSubtype
        fields = ("name",)

    def __init__(self, data=None):
        super().__init__(data, prefix="subtipus")


class ProjectForm(forms.ModelForm):
    class Meta:
        model = EnvironmentalProject
        fields = ("name", "objective", "department")
        widgets = {"objective": _text(2)}

    def __init__(self, data=None):
        super().__init__(data, prefix="projecte")
        self.fields["department"].queryset = Department.objects.filter(active=True)
