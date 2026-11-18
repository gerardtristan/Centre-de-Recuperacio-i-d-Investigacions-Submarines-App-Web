"""T-DX-63: la pàgina «Activitats» del soci (programa de l'escriptori, PR 8). Contingut d'exemple,
inventat i fix; mai cap consulta. Proposta (D1, P-312): depèn dels mòduls 02 i 11 i de S-M02-11.

El soci d'exemple té la titulació B1 i la llicència vigent. «Per a tu» (`can`) i les places són
fixos aquí; quan funcioni, «per a tu» el calcularà el servidor amb les titulacions i la llicència
del soci, i de les places només en dirà el nombre. Els nivells són d'exemple (S-M02-11) i els
llocs, una llista editable (dades, no codi).
"""

from django.utils.translation import gettext_lazy as _

TITLE = _("Activitats")

TYPES = (
    {"key": "sortida", "tab": _("Sortides"), "name": _("Sortida"), "icon": "fish"},
    {
        "key": "curs",
        "tab": _("Cursos i especialitats"),
        "name": _("Curs"),
        "icon": "graduation-cap",
    },
    {
        "key": "conferencia",
        "tab": _("Conferències d'Història"),
        "name": _("Conferència"),
        "icon": "scroll",
    },
    {"key": "medi", "tab": _("Medi ambient"), "name": _("Medi ambient"), "icon": "leaf"},
)
MONTHS = (_("Abril de 2027"), _("Maig de 2027"), _("Juny de 2027"), _("Juliol de 2027"))
SHORT_MONTHS = (_("abr."), _("maig"), _("juny"), _("jul."))
PLACES = (
    ("barcelona", _("Barcelona")),
    ("estartit", _("L'Estartit")),
    ("tossa", _("Tossa de Mar")),
    ("sant-feliu", _("Sant Feliu de Guíxols")),
    ("escala", _("L'Escala")),
    ("cadaques", _("Cadaqués")),
)
_TYPES = {t["key"]: t for t in TYPES}


def _act(kind, title, month, day, when, place, place_key, level, places, saved=False):
    """`level`: None (oberta a tothom), ("ok", "B1") o ("falta", "B2", curs que hi porta)."""
    return {
        "type": _TYPES[kind],
        "title": title,
        "month": month,
        "short_month": SHORT_MONTHS[month],
        "day": day,
        "when": when,
        "place": place,
        "place_key": place_key,
        "level": level,
        "can": level is None or level[0] == "ok",
        "places": places,
        "saved": saved,
    }


_COURSE_B2 = _("Curs de B2, del 03/05")
# fmt: off
ACTS = [
    _act("sortida", _("Sortida a les Medes"), 0, 17, _("Dissabte 17/04 · 08:00"),
         _("L'Estartit"), "estartit", ("ok", "B1"), 4, saved=True),
    _act("sortida", _("Sortida a Tossa"), 0, 18, _("Diumenge 18/04 · 09:00"),
         _("Tossa de Mar"), "tossa", ("ok", "B1"), 10),
    _act("conferencia", _("Els primers bussejadors del club"), 0, 22, _("Dijous 22/04 · 19:30"),
         _("Local del club, Barcelona"), "barcelona", None, 30),
    _act("curs", _("Curs de B2"), 1, 3, _("Del 03/05 al 24/05"),
         _("Piscina i l'Estartit"), "estartit", ("ok", "B1"), 2),
    _act("medi", _("Neteja del fons de la Barceloneta"), 1, 8, _("Dissabte 08/05 · 09:00"),
         _("Barcelona"), "barcelona", ("ok", "B1"), 12),
    _act("sortida", _("Immersió nocturna a Sant Feliu"), 1, 15, _("Dissabte 15/05 · 20:30"),
         _("Sant Feliu de Guíxols"), "sant-feliu", ("falta", "B2", _COURSE_B2), 6),
    _act("curs", _("Especialitat de nitrox"), 1, 22, _("Dissabte 22/05 · 10:00"),
         _("Local del club, Barcelona"), "barcelona", ("ok", "B1"), 0),
    _act("conferencia", _("La costa sota l'aigua, abans i ara"), 1, 27, _("Dijous 27/05 · 19:30"),
         _("Local del club, Barcelona"), "barcelona", None, 18, saved=True),
    _act("sortida", _("Sortida al Cap de Creus"), 2, 12, _("Dissabte 12/06 · 08:00"),
         _("Cadaqués"), "cadaques", ("falta", "B2", _COURSE_B2), 8),
    _act("medi", _("Cens de posidònia"), 2, 19, _("Dissabte 19/06 · 09:30"),
         _("L'Escala"), "escala", ("ok", "B1"), 8),
    _act("sortida", _("Sortida a les Formigues"), 2, 26, _("Dissabte 26/06 · 08:00"),
         _("L'Escala"), "escala", ("falta", "B2", _COURSE_B2), 5),
    _act("curs", _("Especialitat de rescat"), 3, 3, _("Del 03/07 al 17/07"),
         _("Piscina, Barcelona"), "barcelona", ("falta", "B2", _COURSE_B2), 6, saved=True),
]
# fmt: on


def _by_month(acts):
    return [
        {"name": MONTHS[m], "acts": [a for a in acts if a["month"] == m]}
        for m in sorted({a["month"] for a in acts})
    ]


def _section(kind):
    acts = [a for a in ACTS if a["type"] is kind]
    return {**kind, "acts": acts, "months": _by_month(acts)}


_SAVED = [a for a in ACTS if a["saved"]]

CONTEXT = {
    "acts": ACTS,
    "total": len(ACTS),
    "for_you": sum(a["can"] for a in ACTS),
    "for_you_acts": [a for a in ACTS if a["can"]][:3],
    "sections": [_section(t) for t in TYPES],
    "saved": _SAVED,
    "saved_months": _by_month(_SAVED),
    "places": PLACES,
    "member_level": "B1",
}
