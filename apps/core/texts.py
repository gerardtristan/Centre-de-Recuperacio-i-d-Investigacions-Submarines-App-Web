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

import re
from collections import namedtuple
from dataclasses import dataclass, field
from functools import partial

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import dateformat, translation
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from .models import Setting

SECTION = "texts"

# `get` treu el valor del context del correu; `sample` és la dada inventada de la vista prèvia.
Var = namedtuple("Var", "label sample get")


@dataclass(frozen=True)
class EmailText:
    template: str
    label: str
    default: str
    vars: dict = field(default_factory=dict)
    when: object = None


def _date(value) -> str:
    return dateformat.format(value, "d/m/Y")


_AMOUNT = Var(gettext_lazy("import de la quota"), "55,00 €", lambda c: c["amount"])
_DUE_ON = Var(gettext_lazy("data de venciment"), "15/12/2026", lambda c: _date(c["due_on"]))

EMAILS = {
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
    ),
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
        when=lambda c: bool(c.get("overdue")),
    ),
}
TEMPLATES = frozenset(e.template for e in EMAILS.values())

_VAR = re.compile(r"\{([a-z_]+)\}")
_TAG = re.compile(r"<\s*[a-zA-Z/!?]")


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
    if _TAG.search(value):
        raise ValidationError(_("El text no pot portar etiquetes HTML: s'envia com a text pla."))
    unknown = sorted({name for name in _VAR.findall(value) if name not in entry.vars})
    rest = _VAR.sub("", value)
    if unknown or "{" in rest or "}" in rest:
        raise ValidationError(
            _("Les claus { } només serveixen per a les variables d'aquest correu: %(names)s.")
            % {"names": _names(entry)}
        )


def register() -> None:
    from . import business_settings

    for key in EMAILS:
        business_settings.register_check(key, partial(validate, key))


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
    return _(
        "La primera línia és l'assumpte i la resta, el cos del correu. Text pla, sense HTML. "
        "Variables: %(vars)s. Si el deixes buit, torna el text per defecte."
    ) % {"vars": ", ".join(f"{{{n}}} ({v.label})" for n, v in EMAILS[key].vars.items())}


def _fill(text: str, values: dict) -> tuple[str, str]:
    # Una sola passada: el valor d'una variable no es torna a interpretar.
    text = _VAR.sub(lambda m: values[m.group(1)], text)
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
    language = settings.LANGUAGE_CODE if edited else language
    with translation.override(language):
        values = {name: str(var.get(context)) for name, var in entry.vars.items()}
        subject, body = _fill(edited or str(entry.default), values)
    return subject, body, language
