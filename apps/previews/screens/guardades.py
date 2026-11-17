"""T-DX-25 Marcador: les activitats guardades del soci. Contingut d'exemple, inventat i fix."""

from django.utils.translation import gettext_lazy as _

TITLE = _("Activitats guardades")


def _act(title, kind, when, places, saved=False, last=False):
    return {
        "title": title,
        "kind": kind,
        "when": when,
        "places": places,
        "saved": saved,
        "last": last,
    }


CONTEXT = {
    "saved": [
        _act(
            _("Sortida a les Medes"),
            _("Sortida"),
            _("Dissabte 17/04/2027 · 08:00"),
            _("Queden 6 places"),
            saved=True,
        ),
        _act(
            _("Curs Advanced"),
            _("Curs"),
            _("Del 03/05 al 24/05/2027"),
            _("Últimes places"),
            saved=True,
            last=True,
        ),
    ],
    "others": [
        _act(
            _("Sortida a Tossa"),
            _("Sortida"),
            _("Diumenge 18/04/2027 · 09:00"),
            _("Queden 10 places"),
        ),
        _act(_("Curs Open Water"), _("Curs"), _("Del 07/06 al 28/06/2027"), _("Queden 8 places")),
    ],
}
