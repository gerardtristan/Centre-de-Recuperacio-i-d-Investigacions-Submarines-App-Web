"""T-M07-19 Catàleg de blocs de la web pública (decisió 106, RN-M07-15). Contingut d'exemple, fix.

Cada bloc es pinta amb la seva plantilla real, `website/blocs/<kind>.html`, amb un `block` com el
que donarà el renderitzador del 07 (els camps «md» ja convertits; aquí, text pla, que s'escapa)."""

from django.utils.translation import gettext_lazy as _

TITLE = _("Blocs de la web")
CONTEXT = {
    "groups": [
        {
            "name": _("Text"),
            "blocks": [
                {"kind": "heading", "level": 2, "text": _("Bussejar a la Mediterrània")},
                {
                    "kind": "text",
                    "title": _("Qui som"),
                    "body": _(
                        "Text d'exemple: un club de busseig de Barcelona que fa cursos, sortides "
                        "i projectes de medi ambient amb voluntaris."
                    ),
                    "width": "normal",
                },
                {"kind": "heading", "level": 3, "text": _("Sortides de cada mes")},
                {
                    "kind": "quote",
                    "text": _("Text d'exemple: la primera immersió no s'oblida mai."),
                    "attribution": _("Un alumne del curs d'iniciació"),
                    "background": "soft",
                },
                {
                    "kind": "quote",
                    "text": _("Text d'exemple: tenir cura del fons marí és cosa de tots."),
                    "background": "marine",
                },
                {
                    "kind": "list",
                    "title": _("Què cal portar"),
                    "items": [_("Roba de bany"), _("Tovallola"), _("La llicència al dia")],
                    "style": "checks",
                },
                {
                    "kind": "list",
                    "title": _("Com t'hi apuntes"),
                    "items": [_("Tria la sortida"), _("Omple les teves dades"), _("Paga la plaça")],
                    "style": "numbers",
                },
                {
                    "kind": "disclosure",
                    "question": _("Cal saber bussejar per venir a un bateig?"),
                    "answer": _("Text d'exemple: no, el bateig és per a qui no ha bussejat mai."),
                },
                {
                    "kind": "callout",
                    "tone": "info",
                    "title": _("Inscripcions obertes"),
                    "body": _("Text d'exemple: les places de dissabte es tanquen dijous."),
                },
                {
                    "kind": "callout",
                    "tone": "warning",
                    "body": _("Text d'exemple: si fa mala mar, la sortida es pot ajornar."),
                },
            ],
        },
    ],
}
