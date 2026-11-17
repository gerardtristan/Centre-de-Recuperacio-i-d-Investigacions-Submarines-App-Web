"""T-DX-26 Desfile i Oleaje: la portada de la web pública. Contingut d'exemple, inventat i fix.

Desfile sense avanç automàtic (D20; pla dels recursos externs §5). Sense fotos: les del club
necessiten el consentiment de les persones que hi surten (P-41).
"""

from django.utils.translation import gettext_lazy as _

TITLE = _("Portada de la web pública")


def _act(title, kind, when, price):
    return {"title": title, "kind": kind, "when": when, "price": price}


CONTEXT = {
    "acts": [
        _act(_("Sortida a les Medes"), _("Sortida"), _("Dissabte 17/04/2027"), "45,00 €"),
        _act(_("Sortida a Tossa"), _("Sortida"), _("Diumenge 18/04/2027"), "35,00 €"),
        _act(_("Curs Open Water"), _("Curs"), _("Del 07/06 al 28/06/2027"), "320,00 €"),
        _act(_("Curs Advanced"), _("Curs"), _("Del 03/05 al 24/05/2027"), "280,00 €"),
        _act(_("Bateig a la piscina"), _("Bateig"), _("Dissabte 08/05/2027"), "25,00 €"),
    ],
}
