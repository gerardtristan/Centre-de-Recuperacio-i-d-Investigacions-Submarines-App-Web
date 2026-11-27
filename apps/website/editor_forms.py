"""Formulari del bloc triat a l'editor (T-M07-06a), fet de l'esquema del catàleg. Només comprova
els tipus: qui decideix si el bloc és vàlid és `blocks.validate`, en desar (RN-M07-15)."""

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.activities.models import Activity

from . import blocks as catalog
from .models import FaqTopic, MediaAsset

KINDS = {
    "heading": _("Títol"), "text": _("Text"), "quote": _("Cita"), "list": _("Llista"),
    "disclosure": _("Pregunta desplegable"), "callout": _("Avís destacat"),
    "image": _("Imatge"), "gallery": _("Galeria"), "image_text": _("Imatge amb text"),
    "video": _("Vídeo"), "file": _("Fitxer"), "section": _("Secció"),
    "divider": _("Separador"), "spacer": _("Espai"), "button": _("Botó"),
    "join_cta": _("Crida «Fes-te soci»"), "newsletter": _("Subscripció al butlletí"),
    "contact_form": _("Formulari de contacte"), "upcoming_activities": _("Properes activitats"),
    "featured_activities": _("Activitats destacades"), "past_activities": _("Activitats fetes"),
    "recent_news": _("Notícies recents"), "faq_topic": _("Preguntes d'un tema"),
    "key_figures": _("Xifres destacades"), "project_cards": _("Targetes de projectes"),
    "featured_trip": _("Sortida destacada"), "shared": _("Bloc compartit"),
}  # fmt: skip
GROUPS = (
    (_("Text"), ("heading", "text", "quote", "list", "disclosure", "callout")),
    (_("Mitjans"), ("image", "gallery", "image_text", "video", "file")),
    (_("Disposició"), ("divider", "spacer")),  # la secció, sense afegir fins a la P-682
    (_("Acció"), ("button", "join_cta", "newsletter", "contact_form")),
    (_("Dades del club"), ("upcoming_activities", "featured_activities", "past_activities",
     "recent_news", "faq_topic", "key_figures", "project_cards", "featured_trip")),
)  # fmt: skip
LABELS = {
    "text": _("Text"), "level": _("Nivell"), "title": _("Títol"), "body": _("Text"),
    "width": _("Amplada"), "attribution": _("Autoria"), "background": _("Fons"),
    "items": _("Elements"), "style": _("Estil"), "question": _("Pregunta"),
    "answer": _("Resposta"), "tone": _("To"), "media": _("Foto"), "caption": _("Peu de foto"),
    "columns": _("Columnes"), "image_side": _("Costat de la foto"), "source": _("Origen"),
    "youtube_id": _("Identificador del vídeo de YouTube"), "video": _("Vídeo propi"),
    "thumbnail": _("Miniatura"), "file": _("Fitxer (PDF)"), "label": _("Text"),
    "size": _("Mida"), "target": _("Destinació"), "count": _("Quantes"),
    "layout": _("Disposició"), "topic": _("Tema"), "activity": _("Activitat (número)"),
    "value": _("Xifra"), "type": _("Tipus"), "department": _("Departament"),
}  # fmt: skip
CHOICES = {
    "none": _("Cap"), "soft": _("Suau"), "marine": _("Marí"), "accent": _("Accent"),
    "normal": _("Normal"), "wide": _("Ampla"), "full": _("Completa"), "bullets": _("Punts"),
    "numbers": _("Números"), "checks": _("Comprovació"), "info": _("Informació"),
    "warning": _("Avís"), "left": _("Esquerra"), "right": _("Dreta"), "small": _("Petit"),
    "medium": _("Mitjà"), "large": _("Gran"), "secondary": _("Secundari"),
    "primary": _("Principal"), "list": _("Llista"), "cards": _("Targetes"),
    "youtube": _("YouTube"), "own": _("Vídeo propi"),
}  # fmt: skip
HELP = {
    "md": _("Negreta, cursiva, enllaços, llistes i títols. Res d'HTML."),
    "target": _("Una pàgina de la web («/qui-som/») o una adreça que comenci per «https://»."),
    "lines": _("Un element per línia."),
}


def summary(block: dict) -> str:
    """El nom del bloc a la llista: el tipus i el primer text que porti."""
    text = next((block[k] for k in ("title", "text", "label", "question") if block.get(k)), "")
    return f"{KINDS[block['kind']]} · {text[:60]}" if text else str(KINDS[block["kind"]])


def _photos():
    active = MediaAsset.objects.filter(status=MediaAsset.Status.ACTIVE)
    return [(str(a.key), a.alt_text) for a in active if a.publishable]


def _field(name: str, spec: catalog.Field):
    label, t = LABELS.get(name, name), spec.type
    if t in ("text", "md"):
        widget = forms.Textarea(attrs={"rows": 6}) if t == "md" else None
        return forms.CharField(label=label, required=False, max_length=spec.max, widget=widget,
                               help_text=HELP["md"] if t == "md" else "")  # fmt: skip
    if t == "items" and spec.item.type == "media":  # galeria
        return forms.MultipleChoiceField(label=label, choices=_photos(), required=False,
                                         widget=forms.CheckboxSelectMultiple)  # fmt: skip
    if t == "items":
        return forms.CharField(label=label, required=False, help_text=HELP["lines"],
                               widget=forms.Textarea(attrs={"rows": 5}))  # fmt: skip
    if t == "choice":
        options = [(c, CHOICES.get(c, c)) for c in spec.choices]
        return forms.TypedChoiceField(label=label, choices=options, coerce=type(spec.choices[0]))
    if t == "filters" and name == "type":  # curs o sortida (02)
        return forms.ChoiceField(label=label, choices=[("", "—"), *Activity.Kind.choices],
                                 required=False)  # fmt: skip
    if t == "int" and name == "topic":
        topics = [("", "—")] + [(t.pk, t.name) for t in FaqTopic.objects.all()]
        return forms.TypedChoiceField(label=label, choices=topics, coerce=int, required=False)
    if t in ("int", "filters"):  # el departament, pel número fins que hi hagi el selector
        return forms.IntegerField(label=label, required=False, min_value=spec.min or 1)
    if t == "media":
        return forms.ChoiceField(label=label, choices=[("", "—")] + _photos(), required=False)
    if t == "target":
        return forms.CharField(label=label, required=False, max_length=300, help_text=HELP[t])
    return forms.CharField(label=label, required=False, max_length=100)  # ref, youtube


def _fields(kind: str):
    """(nom del camp del formulari, camí dins del bloc, camp) per a cada camp editable."""
    for name, spec in catalog.CATALOG[kind].items():
        if spec.type == "columns":
            continue  # P-682: les columnes d'una secció encara no s'editen
        if spec.type == "filters":
            for sub in ("type", "department"):
                yield f"filters_{sub}", ("filters", sub), spec
        elif spec.type == "items" and isinstance(spec.item, dict):
            for i in range(spec.max):
                for sub, item_spec in spec.item.items():
                    yield f"{name}_{i}_{sub}", (name, i, sub), item_spec
        else:
            yield name, (name,), spec


class BlockForm(forms.Form):
    def __init__(self, kind: str, *args, block=None, **kwargs):
        self.kind, block = kind, block or {}
        super().__init__(*args, **kwargs)
        for form_name, path, spec in _fields(kind):
            field = _field(path[-1], spec)
            if len(path) == 3:
                field.label = f"{LABELS[path[0]]} {path[1] + 1}: {field.label}"
            field.initial = _get(block, path, catalog.CATALOG[kind].get(path[0]))
            self.fields[form_name] = field

    def to_block(self, old: dict) -> dict:
        """El bloc nou amb els camps omplerts; conserva `hidden` i les columnes."""
        new = {k: old[k] for k in ("kind", "hidden", "columns") if k in old}
        new["kind"] = self.kind
        for form_name, path, _spec in _fields(self.kind):
            value = self.cleaned_data.get(form_name)
            parent = catalog.CATALOG[self.kind].get(path[0])
            if _is_list_of(parent, "text"):
                value = [line.strip() for line in (value or "").splitlines() if line.strip()]
            if value in catalog.EMPTY:
                continue
            if len(path) == 1:
                new[path[0]] = value
            elif len(path) == 2:
                new.setdefault(path[0], {})[path[1]] = value
            else:
                items = new.setdefault(path[0], [])
                while len(items) <= path[1]:
                    items.append({})
                items[path[1]][path[2]] = value
        return {k: [i for i in v if i != {}] if isinstance(v, list) else v for k, v in new.items()}


def _is_list_of(spec, item_type: str) -> bool:
    return bool(spec) and spec.type == "items" and getattr(spec.item, "type", None) == item_type


def _get(block: dict, path: tuple, parent):
    if len(path) == 1:
        value = block.get(path[0])
        if _is_list_of(parent, "text"):
            return "\n".join(value or [])
        return value
    if len(path) == 2:
        return (block.get(path[0]) or {}).get(path[1])
    items = block.get(path[0]) or []
    return items[path[1]].get(path[2]) if path[1] < len(items) else None
