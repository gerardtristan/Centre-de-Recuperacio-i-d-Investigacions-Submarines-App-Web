"""Plantilles de pàgina amb contingut d'exemple (T-M07-20b, decisió 106). La llista és tancada i és
codi (`Page.Template`); el contingut d'exemple surt de la web actual del club
(`docs/web/contingut-cris1954/`) i es pot canviar tot a l'editor. Les fotos són les primeres de la
biblioteca que es poden publicar (en local, les de la 107 que carrega `seed_demo_data`); si no
n'hi ha, el bloc es queda sense foto i el revisor de qualitat ho avisa.
"""

from django.utils.translation import gettext as _

from .models import MediaAsset, Page

T = Page.Template


def _photos(count: int) -> list[str]:
    active = MediaAsset.objects.filter(status=MediaAsset.Status.ACTIVE).order_by("uploaded_at")
    return [str(a.key) for a in active if a.publishable][:count]


def _with(block: dict, **media) -> dict:
    """El bloc amb les fotos que hi hagi (cap camp buit, que és el que espera l'esborrany)."""
    return {**block, **{k: v for k, v in media.items() if v}}


def example(template: str) -> list[dict]:
    photos = _photos(6) + [None] * 6
    first, second = photos[0], photos[1]
    gallery = [p for p in photos if p]
    welcome = _("El C.R.I.S. va néixer com a club esportiu dedicat al busseig l'any **1954**: "
                "és el primer centre esportiu de busseig de la península Ibèrica. Hem conservat "
                "la filosofia de l'inici: el respecte i l'amor al mar.")  # fmt: skip
    courses = _("Podem començar amb un **bateig** per veure com ens va respirar sota l'aigua i "
                "continuar amb el curs d'iniciació (B1E), que permet fer immersions fins als 25 "
                "metres amb seguretat i a qualsevol lloc del món; després, el B2E… i així fins a "
                "instructor.")  # fmt: skip
    join = {
        "kind": "join_cta",
        "title": _("Fes-te soci"),
        "body": _("Cursos, sortides i activitats tot l'any amb el club."),
        "background": "accent",
    }
    pages = {
        T.HOME: [
            {"kind": "heading", "text": _("Bussejar a la Mediterrània des de 1954"), "level": 2},
            _with({"kind": "image_text", "title": _("Qui som"), "body": welcome}, media=first),
            {"kind": "upcoming_activities", "title": _("Properes activitats"), "count": 3,
             "layout": "cards"},
            {"kind": "key_figures", "items": [{"value": "1954", "label": _("any de fundació")},
                                              {"value": "+70", "label": _("anys al mar")}]},
            join,
        ],
        T.SECTION: [
            {"kind": "heading", "text": _("Formació i cursos"), "level": 2},
            {"kind": "text", "body": courses},
            _with({"kind": "image", "caption": _("Un curs del club")}, media=first),
            {"kind": "button", "label": _("Escriu-nos"), "target": "/contacte/"},
        ],
        T.ARTICLE: [
            {"kind": "text", "title": _("Setanta anys al mar"), "body": welcome},
            {"kind": "quote", "text": _("El mar no és nostre: l'hem de desar als nostres fills en "
                                        "les millors condicions.")},
            _with({"kind": "image"}, media=second),
        ],
        T.PROJECT: [
            _with({"kind": "image_text", "title": _("Un projecte del club"),
                   "body": _("Què fem, on i amb qui. Explica'l aquí.")}, media=first),
            {"kind": "key_figures", "items": [{"value": "0", "label": _("xifra d'exemple")},
                                              {"value": "0", "label": _("una altra xifra")}]},
            {"kind": "project_cards", "items": [_with(
                {"title": _("Vols participar-hi?"), "body": _("Escriu-nos i t'explicarem com."),
                 "target": "/contacte/"}, media=second)]},
        ],
        T.GALLERY: [
            {"kind": "text", "title": _("Galeria"), "body": _("Fotos de les sortides del club.")},
            _with({"kind": "gallery", "columns": 3}, media=gallery if len(gallery) > 1 else None),
        ],
        T.JOIN: [
            join,
            {"kind": "list", "title": _("Què hi trobaràs"), "style": "checks",
             "items": [_("Cursos de tots els nivells"), _("Sortides tot l'any"),
                       _("Activitats i trobades del club")]},
            {"kind": "disclosure", "question": _("Cal tenir experiència?"),
             "answer": _("No: pots començar amb un bateig.")},
        ],
    }  # fmt: skip
    return pages.get(template, [])
