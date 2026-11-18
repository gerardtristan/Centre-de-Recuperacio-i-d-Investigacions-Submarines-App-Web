"""T-DX-63: el bloc «Activitats per a tu» de la portada del soci, sol (la portada l'inclourà més
endavant). Mateix contingut d'exemple que la pàgina Activitats."""

from django.utils.translation import gettext_lazy as _

from .activitats import CONTEXT as _ACTIVITATS

TITLE = _("Activitats per a tu (bloc de la portada)")

CONTEXT = {key: _ACTIVITATS[key] for key in ("for_you_acts", "total")}
