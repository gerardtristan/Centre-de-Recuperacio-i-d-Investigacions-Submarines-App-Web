"""Formularis de les pantalles d'administració del 02 (T-M02-05 i T-M02-06).

Només recullen i normalitzen el que escriu la persona. Les regles de negoci són als serveis
(`catalogue`, `services`, `states` i `sessions`), que les tornen a comprovar totes: un formulari
que es deixi passar una dada no dona cap dret.

- Els imports s'escriuen en euros («45» o «45,50») i es desen en cèntims.
- Les llistes desplegables només ofereixen el que es pot triar: fitxes, tipus, subtipus i
  departaments actius, i persones que poden fer aquell paper. No s'hi llista mai tot el cens.
"""

import re

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.models import Department, Person
from apps.core.permissions import accounts_with_perm

from . import permissions, sessions
from .models import (
    Activity,
    EnvironmentalProject,
    EnvironmentalSubtype,
    OutingType,
    Session,
    TrainingCatalogueEntry,
)

DATE_ERROR = _("Escriu una data vàlida, per exemple 14/06/2027.")
MOMENT_ERROR = _("Escriu el dia i l'hora, per exemple 14/06/2027 09:00.")
TIME_ERROR = _("Escriu una hora vàlida, per exemple 09:30.")
_EUROS = re.compile(r"^(\d{1,6})(?:[.,](\d{1,2}))?$")


class EuroField(forms.Field):
    """Un import en euros que es desa en cèntims (enter). «45», «45,5» i «45.50» valen."""

    widget = forms.TextInput
    default_error_messages = {
        "invalid": _("Escriu l'import en euros, per exemple 45 o 45,50."),
    }

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


def _date(label, **kwargs):
    return forms.DateField(
        label=label,
        input_formats=["%Y-%m-%d", "%d/%m/%Y"],
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        error_messages={"invalid": DATE_ERROR},
        **kwargs,
    )


def _moment(label, **kwargs):
    return forms.DateTimeField(
        label=label,
        input_formats=["%Y-%m-%dT%H:%M", "%d/%m/%Y %H:%M"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        error_messages={"invalid": MOMENT_ERROR},
        **kwargs,
    )


def _departments():
    return Department.objects.filter(active=True).order_by("name")


def _text(rows=4):
    return forms.Textarea(attrs={"rows": rows})


# --- Catàleg (T-M02-05) ---------------------------------------------------------------------------


class CatalogueEntryForm(forms.Form):
    """Fitxa del catàleg. Els preus només s'escriuen en crear-la: després tenen el seu formulari,
    amb motiu i data d'entrada en vigor."""

    name = forms.CharField(label=_("Nom"), max_length=120)
    level = forms.CharField(
        label=_("Nivell"),
        max_length=60,
        required=False,
        help_text=_("El nivell que dona o que demana, si en té."),
    )
    description = forms.CharField(label=_("Descripció"), required=False, widget=_text())
    requirements = forms.CharField(label=_("Requisits"), required=False, widget=_text(3))
    default_places = forms.IntegerField(label=_("Places per defecte"), min_value=1, max_value=500)
    price_member_cents = EuroField(label=_("Preu de soci"))
    price_non_member_cents = EuroField(label=_("Preu de no soci"))
    reinforcement_price_cents = EuroField(
        label=_("Preu d'una classe de reforç"),
        required=False,
        help_text=_("En euros. Es pot deixar en blanc."),
    )
    open_to_non_members = forms.BooleanField(label=_("Oberta a no socis"), required=False)
    department = forms.ModelChoiceField(label=_("Departament"), queryset=Department.objects.none())

    PRICES = ("price_member_cents", "price_non_member_cents", "reinforcement_price_cents")
    EDITABLE = (
        "name",
        "level",
        "description",
        "requirements",
        "default_places",
        "open_to_non_members",
        "department",
    )

    def __init__(self, data=None, *, entry=None):
        initial = {name: getattr(entry, name) for name in self.EDITABLE} if entry else {}
        super().__init__(data, initial=initial)
        self.fields["department"].queryset = _departments()
        if entry is not None:
            for name in self.PRICES:
                del self.fields[name]


class PriceChangeForm(forms.Form):
    price_member_cents = EuroField(label=_("Preu de soci"))
    price_non_member_cents = EuroField(label=_("Preu de no soci"))
    reinforcement_price_cents = EuroField(
        label=_("Preu d'una classe de reforç"),
        required=False,
        help_text=_("En euros. Es pot deixar en blanc."),
    )
    valid_from = _date(
        _("En vigor des del"),
        help_text=_("Avui o més endavant. Les activitats ja creades no canvien."),
    )
    note = forms.CharField(
        label=_("Motiu"),
        widget=_text(3),
        help_text=_("Queda al registre i s'envia al tresorer i a la junta."),
        error_messages={"required": _("Cal escriure el motiu del canvi de preu.")},
    )

    def __init__(self, data=None, *, current, today):
        initial = {
            "price_member_cents": current.member_cents,
            "price_non_member_cents": current.non_member_cents,
            "reinforcement_price_cents": current.reinforcement_cents,
            "valid_from": today,
        }
        super().__init__(data, initial=initial)


class OutingTypeForm(forms.Form):
    prefix = "tipus"
    name = forms.CharField(label=_("Nom del tipus"), max_length=80)
    is_environmental = forms.BooleanField(
        label=_("És de medi ambient (té subtipus i projecte)"), required=False
    )
    default_department = forms.ModelChoiceField(
        label=_("Departament per defecte"), queryset=Department.objects.none()
    )

    def __init__(self, data=None):
        super().__init__(data)
        self.fields["default_department"].queryset = _departments()


class SubtypeForm(forms.Form):
    prefix = "subtipus"
    name = forms.CharField(label=_("Nom del subtipus"), max_length=80)


class ProjectForm(forms.Form):
    name = forms.CharField(label=_("Nom del projecte"), max_length=120)
    objective = forms.CharField(
        label=_("Objectiu"),
        widget=_text(3),
        error_messages={"required": _("Cal escriure l'objectiu del projecte.")},
    )
    department = forms.ModelChoiceField(label=_("Departament"), queryset=Department.objects.none())

    def __init__(self, data=None):
        super().__init__(data)
        self.fields["department"].queryset = _departments()


# --- Activitats (T-M02-06) ------------------------------------------------------------------------


class EntryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, entry):
        return f"{entry.get_kind_display()}: {entry.name}"


def responsible_people():
    """Qui pot ser responsable d'una activitat: les persones amb un compte que pot gestionar
    activitats (AC7 amb edició). No s'hi llista cap altra persona del club."""
    accounts = accounts_with_perm(permissions.MANAGE, write=True)
    return Person.objects.filter(
        pk__in=[account.person_id for account in accounts], status=Person.Status.ACTIVE
    ).order_by("first_name", "last_name", "pk")


class ActivityForm(forms.Form):
    """Crear o editar un curs o una sortida. En un curs nou, les places i els preus es poden
    deixar en blanc: es copien de la fitxa del catàleg."""

    catalogue_entry = EntryChoiceField(
        label=_("Fitxa del catàleg"),
        queryset=TrainingCatalogueEntry.objects.none(),
        help_text=_("Se'n copien les places, els preus vigents avui i el departament."),
    )
    outing_type = forms.ModelChoiceField(
        label=_("Tipus de sortida"), queryset=OutingType.objects.none()
    )
    subtype = forms.ModelChoiceField(
        label=_("Subtipus"),
        queryset=EnvironmentalSubtype.objects.none(),
        required=False,
        help_text=_("Només per a les sortides de medi ambient, que n'han de tenir."),
    )
    project = forms.ModelChoiceField(
        label=_("Projecte"),
        queryset=EnvironmentalProject.objects.none(),
        required=False,
        help_text=_("Només per a les sortides de medi ambient. És opcional."),
    )
    title = forms.CharField(label=_("Títol"), max_length=140)
    description = forms.CharField(label=_("Descripció o objectiu"), required=False, widget=_text())
    starts_on = _date(_("Data d'inici"))
    ends_on = _date(_("Data de final"))
    location = forms.CharField(label=_("Lloc"), max_length=140, required=False)
    meeting_point = forms.CharField(label=_("Punt de trobada"), max_length=140, required=False)
    registration_closes_at = _moment(
        _("Data límit d'inscripció"), help_text=_("Com a molt tard, el dia d'inici.")
    )
    max_places = forms.IntegerField(label=_("Places"), min_value=1, max_value=500)
    price_member_cents = EuroField(label=_("Preu de soci"))
    price_non_member_cents = EuroField(label=_("Preu de no soci"))
    price_override_note = forms.CharField(
        label=_("Motiu del preu diferent del catàleg"),
        required=False,
        widget=_text(2),
        help_text=_("Obligatori si algun preu és diferent del catàleg. S'avisa el tresorer."),
    )
    payment_window_hours = forms.IntegerField(
        label=_("Termini de pagament (hores)"), min_value=1, max_value=720, required=False
    )
    open_to_non_members = forms.BooleanField(label=_("Oberta a no socis"), required=False)
    required_level = forms.CharField(label=_("Titulació mínima"), max_length=60, required=False)
    licence_required = forms.BooleanField(label=_("Cal llicència vigent"), required=False)
    requirements_mode = forms.ChoiceField(
        label=_("Si algú no compleix els requisits"),
        choices=Activity.RequirementsMode.choices,
        required=False,
    )
    responsible = forms.ModelChoiceField(
        label=_("Persona responsable"), queryset=Person.objects.none()
    )
    department = forms.ModelChoiceField(
        label=_("Departament"), queryset=Department.objects.none(), required=False
    )
    forecast_url = forms.CharField(
        label=_("Enllaç a la previsió marítima"),
        max_length=200,
        required=False,
        help_text=_("Una adreça que comenci per https://. Només s'hi posa l'enllaç."),
    )

    COURSE_ONLY = ("catalogue_entry",)
    OUTING_ONLY = ("outing_type", "subtype", "project")
    COPIED_FROM_ENTRY = ("max_places", "price_member_cents", "price_non_member_cents")
    OPTIONAL_DEFAULTS = ("payment_window_hours", "requirements_mode", "department")

    def __init__(self, data=None, *, kind, activity=None, user=None):
        self.kind, self.activity = kind, activity
        initial = {}
        if activity is not None:
            initial = {name: getattr(activity, name) for name in self.base_fields}
        elif user is not None:
            initial = {"responsible": user.person_id}
        super().__init__(data, initial=initial)
        course = kind == Activity.Kind.COURSE
        for name in self.OUTING_ONLY if course else self.COURSE_ONLY:
            del self.fields[name]
        people = responsible_people()
        if activity is not None:
            # Qui ja n'és responsable s'hi manté encara que ara no tingui el permís.
            people = Person.objects.filter(
                pk__in=[activity.responsible_id, *(person.pk for person in people)]
            ).order_by("first_name", "last_name", "pk")
        self.fields["responsible"].queryset = people
        self.fields["department"].queryset = _departments()
        if course and activity is None:
            self.fields["catalogue_entry"].queryset = TrainingCatalogueEntry.objects.filter(
                active=True
            ).order_by("kind", "name")
            for name in self.COPIED_FROM_ENTRY:
                self.fields[name].required = False
                self.fields[name].help_text = _("En blanc, es copia de la fitxa del catàleg.")
        elif course:
            del self.fields["catalogue_entry"]  # la fitxa no es canvia mai
        else:
            self.fields["outing_type"].queryset = OutingType.objects.filter(active=True)
            self.fields["subtype"].queryset = EnvironmentalSubtype.objects.filter(active=True)
            self.fields["project"].queryset = EnvironmentalProject.objects.filter(
                status=EnvironmentalProject.Status.ACTIVE
            )
            if activity is not None:
                # El que ja té triat s'hi manté encara que ara estigui desactivat.
                for name, model in (
                    ("outing_type", OutingType),
                    ("subtype", EnvironmentalSubtype),
                    ("project", EnvironmentalProject),
                ):
                    current = getattr(activity, f"{name}_id")
                    self.fields[name].queryset = (
                        self.fields[name].queryset | model.objects.filter(pk=current)
                    ).distinct()
        if activity is not None:
            for name in self.OPTIONAL_DEFAULTS:
                self.fields[name].required = True

    def service_data(self) -> dict:
        """Les dades tal com les esperen `services.create_*` i `services.update_activity`: el
        que s'ha deixat en blanc perquè es copiï o prengui el valor per defecte no s'hi posa."""
        data = dict(self.cleaned_data)
        if self.activity is None:
            for name in (*self.COPIED_FROM_ENTRY, *self.OPTIONAL_DEFAULTS):
                if name in data and data[name] in (None, ""):
                    del data[name]
        return data


class ReopenForm(forms.Form):
    closes_at = _moment(
        _("Data límit d'inscripció nova"),
        required=False,
        help_text=_(
            "Cal si la data límit actual ja ha passat. Ha de ser futura i, com a molt tard, "
            "el dia d'inici."
        ),
    )


class ReasonForm(forms.Form):
    reason = forms.CharField(
        label=_("Motiu"),
        widget=_text(3),
        max_length=1000,
        help_text=_("Queda al registre d'activitat. Sense dades de salut."),
        error_messages={"required": _("Cal escriure el motiu de la cancel·lació.")},
    )


class InstructorsField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, person):
        return str(person)


class SessionForm(forms.Form):
    kind = forms.ChoiceField(label=_("Classe de sessió"), choices=Session.Kind.choices)
    starts_at = _moment(_("Comença"))
    ends_at = _moment(_("Acaba"))
    location = forms.CharField(label=_("Lloc"), max_length=140, required=False)
    is_practice = forms.BooleanField(label=_("És una pràctica (s'hi avalua)"), required=False)
    instructors = InstructorsField(
        label=_("Instructors"),
        queryset=Person.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    FIELDS = ("kind", "starts_at", "ends_at", "location", "is_practice")

    def __init__(self, data=None, *, session=None):
        initial = {}
        if session is not None:
            initial = {name: getattr(session, name) for name in self.FIELDS}
            initial["instructors"] = list(session.instructors.values_list("pk", flat=True))
        super().__init__(data, initial=initial)
        self.fields["instructors"].queryset = sessions.instructor_people().order_by(
            "first_name", "last_name", "pk"
        )


class ProgrammeForm(forms.Form):
    """El programa del dia sencer: una fila per bloc, en ordre. Les files buides no compten."""

    EXTRA = 3
    MIN_ROWS = 5
    COLUMNS = ("starts_at", "ends_at", "label", "location", "responsible_label")

    def __init__(self, data=None, *, blocks=()):
        super().__init__(data)
        blocks = list(blocks)
        self.rows = max(len(blocks) + self.EXTRA, self.MIN_ROWS)
        for index in range(self.rows):
            block = blocks[index] if index < len(blocks) else None
            for name, field in self._row_fields().items():
                key = f"{name}_{index}"
                self.fields[key] = field
                if block is not None:
                    self.initial[key] = getattr(block, name)

    @staticmethod
    def _row_fields():
        def time(label):
            return forms.TimeField(
                label=label,
                required=False,
                input_formats=["%H:%M", "%H:%M:%S"],
                widget=forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
                error_messages={"invalid": TIME_ERROR},
            )

        return {
            "starts_at": time(_("Hora d'inici")),
            "ends_at": time(_("Hora de final")),
            "label": forms.CharField(label=_("Què s'hi fa"), max_length=80, required=False),
            "location": forms.CharField(label=_("Lloc"), max_length=140, required=False),
            "responsible_label": forms.CharField(
                label=_("Qui se n'encarrega (funció)"),
                max_length=80,
                required=False,
                help_text=_("Una funció, com «cap d'immersió». Mai un correu ni un telèfon."),
            ),
        }

    def grouped(self):
        """Els camps fila per fila, per a la plantilla."""
        return [
            (index + 1, [self[f"{name}_{index}"] for name in self.COLUMNS])
            for index in range(self.rows)
        ]

    def blocks(self) -> list[dict]:
        rows = []
        for index in range(self.rows):
            row = {name: self.cleaned_data.get(f"{name}_{index}") for name in self.COLUMNS}
            if any(value not in (None, "") for value in row.values()):
                rows.append(row)
        return rows
