"""Textos editables sense tocar el codi (T-M00-08; decisió 085, S-1 i S-3).

Cada correu editable és un ajust de text de l'apartat «texts» (peça comuna d'ajustos, 055): les
versions, l'historial amb el valor anterior, la nota, el permís i el registre d'activitat són
els de `business_settings.change`. Aquí només hi ha el que és propi dels textos:

- El text per defecte és al codi, traduïble. Un ajust buit (el valor inicial) vol dir «text per
  defecte»; desar-lo buit hi torna.
- Format: la primera línia és l'assumpte i la resta, el cos. Text pla: el correu editat no té
  part HTML i el text no pot portar etiquetes.
- Seguretat: el text mai no es tracta com una plantilla de Django. Només s'hi substitueixen, en
  una sola passada, les variables `{nom}` de la llista del correu; qualsevol altra clau `{` `}`
  es rebutja en desar-lo.
- Un correu amb variants (p. ex. abans i després del venciment) té un text per variant; `when`
  tria la variant a partir del context.
"""

import logging
import re
from collections import namedtuple
from dataclasses import dataclass, field
from functools import partial

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import dateformat, translation
from django.utils.functional import lazy
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from .models import Setting

# Àrea dels textos (T-M00-08d): cada àrea és un apartat d'ajustos, `settings.section.<àrea>`.
# Ara tots els correus editables són de l'àrea de socis.
SECTION = "texts-members"
SUBJECT_MAX = 200
logger = logging.getLogger(__name__)

# `get` treu el valor del context del correu; `sample` és la dada inventada de la vista prèvia.
Var = namedtuple("Var", "label sample get")


@dataclass(frozen=True)
class EmailText:
    template: str
    label: str
    default: str
    vars: dict = field(default_factory=dict)
    when: object = None
    # Variables sense les quals el correu ja no té sentit (097, CA-M00-08.2).
    required: tuple = ()


def _date(value) -> str:
    return dateformat.format(value, "d/m/Y")


_AMOUNT = Var(gettext_lazy("import de la quota"), "55,00 €", lambda c: c["amount"])
_DUE_ON = Var(gettext_lazy("data de venciment"), "15/12/2026", lambda c: _date(c["due_on"]))


def _downgrade(context) -> str:
    """Estat del pas a simpatitzant per triar la variant; qualsevol altre valor fa servir el
    text general (com l'antic `{% else %}`)."""
    state = context.get("downgrade")
    return state if state in ("accepted", "pending") else ""


# El paràgraf del pas a simpatitzant és l'única diferència entre les tres variants.
_RENEWAL = gettext_lazy(
    "La teva quota del C.R.I.S. es renova d'aquí a poc\n\nHola,\n\n"
    "La teva quota de soci de ple dret es renova el {data}.\n\n"
    "%(downgrade)s\n\n"
    "Si tens cap dubte, respon aquest correu."
)

EMAILS = {
    # T-M01-17: text aprovat (085, S-1/S-3). No diu res de les quotes
    # pendents (RN-M01-20, P-50) ni del compte personal (Q-31).
    f"{SECTION}.baixa-efectiva": EmailText(
        "baixa-efectiva",
        gettext_lazy("Correu de baixa efectiva"),
        gettext_lazy(
            "La teva baixa al C.R.I.S. és efectiva\n\nHola,\n\n"
            "La teva baixa com a soci és efectiva des del {data}.\n\n"
            "El teu número de soci queda reservat: si algun dia tornes, el recuperaràs.\n\n"
            "Si tens cap dubte, respon aquest correu."
        ),
        {
            "data": Var(
                gettext_lazy("data de la baixa"), "31/12/2026", lambda c: _date(c["effective_on"])
            )
        },
        required=("data",),
    ),
    # T-M01-18 (Q-061 de la 072): text aprovat (085, S-1/S-3), també el de
    # la quota vençuda. Sense cap dada personal: només l'import i el venciment.
    f"{SECTION}.recordatori-quota": EmailText(
        "recordatori-quota",
        gettext_lazy("Recordatori de quota abans del venciment"),
        gettext_lazy(
            "Recordatori: la teva quota del C.R.I.S.\n\nHola,\n\n"
            "La teva quota de soci de {import} venç el {data}.\n\n"
            "Si ja l'has pagada, no cal que facis res.\n\n"
            "Si tens cap dubte, respon aquest correu."
        ),
        {"import": _AMOUNT, "data": _DUE_ON},
        required=("import", "data"),
        when=lambda c: not c.get("overdue"),
    ),
    f"{SECTION}.recordatori-quota-vencuda": EmailText(
        "recordatori-quota",
        gettext_lazy("Recordatori de quota vençuda (impagada)"),
        gettext_lazy(
            "Tens una quota del C.R.I.S. pendent de pagar\n\nHola,\n\n"
            "La teva quota de soci de {import} va vèncer el {data} i encara no consta com a "
            "pagada.\n\n"
            "Si ja l'has pagada, no cal que facis res.\n\n"
            "Si tens cap dubte, respon aquest correu."
        ),
        {"import": _AMOUNT, "data": _DUE_ON},
        required=("import", "data"),
        when=lambda c: bool(c.get("overdue")),
    ),
    # Avís de renovació (073, T-M01-43): un text per a cada estat del pas a simpatitzant.
    # Text aprovat (085, S-1/S-3; 073, punt 6; 085, T-6). Sense cap
    # import ni cap dada personal: només la data de renovació.
    **{
        f"{SECTION}.avis-renovacio{suffix}": EmailText(
            "avis-renovacio",
            label,
            lazy(lambda p: str(_RENEWAL) % {"downgrade": p}, str)(paragraph),
            {
                "data": Var(
                    gettext_lazy("data de renovació"), "15/01/2027", lambda c: _date(c["renews_on"])
                )
            },
            when=lambda c, state=state: _downgrade(c) == state,
            required=("data",),
        )
        for suffix, state, label, paragraph in (
            (
                "",
                "",
                gettext_lazy("Avís de renovació"),
                gettext_lazy(
                    "Si vols passar a simpatitzant en aquesta renovació, demana-ho a «Canvi de "
                    "tipus», al teu perfil, abans del cobrament de la nova quota. El canvi no "
                    "comporta cap devolució de la quota del període actual."
                ),
            ),
            (
                "-pas-acceptat",
                "accepted",
                gettext_lazy("Avís de renovació amb el pas a simpatitzant acceptat"),
                gettext_lazy(
                    "Tens acceptat el pas a simpatitzant: en aquesta renovació passaràs a "
                    "simpatitzant i la quota nova serà la d'aquest tipus."
                ),
            ),
            (
                "-pas-pendent",
                "pending",
                gettext_lazy("Avís de renovació amb el pas a simpatitzant pendent"),
                gettext_lazy(
                    "Tens una sol·licitud de pas a simpatitzant pendent: la secretaria la "
                    "revisarà i, si l'accepta, passaràs a simpatitzant en aquesta renovació."
                ),
            ),
        )
    },
    # T-M01-13: text aprovat (085, S-1/S-3). Cap dada de la persona: el
    # text és el mateix tant si el document ja existia com si no (CA-M01-02).
    f"{SECTION}.rebut-sollicitud-alta": EmailText(
        "rebut-sollicitud-alta",
        gettext_lazy("Rebut de la sol·licitud d'alta"),
        gettext_lazy(
            "Hem rebut la teva sol·licitud d'alta al C.R.I.S.\n\nHola,\n\n"
            "Hem rebut una sol·licitud d'alta com a soci del C.R.I.S. amb aquesta adreça de "
            "correu.\n\n"
            "Aquest correu només confirma que l'hem rebuda: encara no és una alta aprovada. "
            "L'administració del C.R.I.S. la revisarà i t'avisarà per correu.\n\n"
            "Si no has demanat l'alta, no cal que facis res."
        ),
    ),
    # T-M01-14: text aprovat (085, S-1/S-3). Cap dada de la persona i
    # sense motiu (079, P-69, RN-M01-88).
    f"{SECTION}.alta-rebutjada": EmailText(
        "alta-rebutjada",
        gettext_lazy("Sol·licitud d'alta rebutjada"),
        gettext_lazy(
            "La teva sol·licitud d'alta al C.R.I.S.\n\nHola,\n\n"
            "L'administració del C.R.I.S. ha revisat la sol·licitud d'alta com a soci feta amb "
            "aquestes dades i no l'ha pogut aprovar.\n\n"
            "Si tens cap dubte, respon a aquest correu.\n\n"
            "Si no has demanat l'alta, no cal que facis res."
        ),
    ),
}
TEMPLATES = frozenset(e.template for e in EMAILS.values())

_VAR = re.compile(r"\{([a-z_]+)\}")
# Només el que sembla una etiqueta (`<a ...>`, `</p>`, `<br/>`, `<!--`), no «<menys de 50 €».
_TAG = re.compile(r"<!--|</?[a-zA-Z][a-zA-Z0-9-]*(\s[^<>]*)?/?>")


def looks_like_html(value: str) -> bool:
    return bool(_TAG.search(value))


def _names(entry: EmailText) -> str:
    return ", ".join(f"{{{name}}}" for name in entry.vars) or "—"


def validate(key: str, value: str) -> None:
    """Regla del text editat (es registra a `business_settings`). Buit: el text per defecte."""
    if value == "":
        return
    entry = EMAILS[key]
    subject, _sep, body = value.partition("\n")
    if not subject.strip() or not body.strip():
        raise ValidationError(
            _("La primera línia és l'assumpte i, a sota, el cos del correu: calen tots dos.")
        )
    if len(subject.strip()) > SUBJECT_MAX:
        raise ValidationError(
            _("L'assumpte (la primera línia) pot tenir com a màxim %(max)s caràcters.")
            % {"max": SUBJECT_MAX}
        )
    if _TAG.search(value):
        raise ValidationError(_("El text no pot portar etiquetes HTML: s'envia com a text pla."))
    missing = [f"{{{name}}}" for name in entry.required if f"{{{name}}}" not in value]
    if missing:
        raise ValidationError(
            _("Falta una variable obligatòria d'aquest correu: %(names)s.")
            % {"names": ", ".join(missing)}
        )
    unknown = sorted({name for name in _VAR.findall(value) if name not in entry.vars})
    rest = _VAR.sub("", value)
    if unknown or "{" in rest or "}" in rest:
        raise ValidationError(
            _("Les claus { } només serveixen per a les variables d'aquest correu: %(names)s.")
            % {"names": _names(entry)}
        )


def is_editable(setting) -> bool:
    return setting.module == SECTION and setting.key in EMAILS


def normalise_lines(value):
    # El navegador envia els salts com a CR LF.
    return value.replace("\r\n", "\n") if isinstance(value, str) else value


def normalise(key: str, value):
    """Salts de línia uniformes; el text per defecte desat sense canvis es desa buit, perquè
    continuï sent «per defecte» (i traduïble)."""
    value = normalise_lines(value)
    default = str(EMAILS[key].default)
    return "" if isinstance(value, str) and value.strip() == default.strip() else value


def register() -> None:
    from . import business_settings

    for key in EMAILS:
        business_settings.register_check(
            key, partial(validate, key), normalise=partial(normalise, key)
        )


def _edited(key: str) -> str:
    from . import business_settings

    try:
        return business_settings.get(key)
    except Setting.DoesNotExist:  # la base de dades d'una prova sense les dades de la migració
        return ""


def current(key: str) -> str:
    """El text que s'envia ara: l'editat o, si no n'hi ha, el per defecte."""
    return _edited(key) or str(EMAILS[key].default)


def status(key: str) -> str:
    return _("Editat") if _edited(key) else _("Text per defecte")


def help_text(key: str) -> str:
    entry = EMAILS[key]
    names = ", ".join(f"{{{n}}} ({v.label})" for n, v in entry.vars.items())
    text = _(
        "La primera línia és l'assumpte i la resta, el cos del correu. Text pla, sense HTML. "
        "Variables: %(vars)s. Si el deixes buit, torna el text per defecte."
    ) % {"vars": names or _("aquest correu no té variables")}
    if entry.required:
        required = ", ".join(f"{{{n}}}" for n in entry.required)
        text += " " + _("Variables obligatòries: %(names)s.") % {"names": required}
    return text


def _fill(text: str, values: dict) -> tuple[str, str]:
    # Una sola passada: el valor d'una variable no es torna a interpretar. Una variable sense
    # valor es queda com és: un correu no deixa mai de sortir per un text.
    def value(match):
        if match.group(1) in values:
            return values[match.group(1)]
        logger.warning("Variable sense valor en un text de correu: %s", match.group(1))
        return match.group(0)

    text = _VAR.sub(value, normalise_lines(text))
    subject, _sep, body = text.partition("\n")
    return " ".join(subject.split()), body.strip("\n") + "\n"


def preview(key: str, value: str) -> tuple[str, str]:
    """Assumpte i cos amb les dades inventades de cada variable. No desa res."""
    entry = EMAILS[key]
    return _fill(value or str(entry.default), {n: str(v.sample) for n, v in entry.vars.items()})


def render_email(template: str, context: dict, language: str) -> tuple[str, str, str]:
    """Assumpte, cos i llengua d'un correu editable. El text editat és en català: no té
    traduccions fins que es decideixi la P-49 (061)."""
    key, entry = next(
        (k, e)
        for k, e in EMAILS.items()
        if e.template == template and (e.when is None or e.when(context))
    )
    edited = _edited(key)
    with translation.override(language):
        text = edited or str(entry.default)
    with translation.override(settings.LANGUAGE_CODE):
        original = str(entry.default)
    # La llengua en què és el text: l'editat i el que no té traducció són en català.
    if edited or text == original:
        language = settings.LANGUAGE_CODE
    with translation.override(language):
        values = {name: str(var.get(context)) for name, var in entry.vars.items()}
    subject, body = _fill(text, values)
    return subject, body, language
