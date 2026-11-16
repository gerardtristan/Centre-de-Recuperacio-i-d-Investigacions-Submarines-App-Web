"""T-DX-28 Recoveco: l'ajuda i les preguntes freqüents. Contingut d'exemple, inventat i fix."""

from django.utils.translation import gettext_lazy as _

TITLE = _("Ajuda i preguntes freqüents")
CONTEXT = {
    # Respostes d'exemple: no diuen cap regla del club com si fos real ni revelen cap compte.
    "topics": [
        {
            "id": "tema-compte",
            "roman": "I",
            "name": _("El compte"),
            "questions": [
                {
                    "id": "compte-contrasenya",
                    "q": _("He oblidat la contrasenya. Què faig?"),
                    "a": _(
                        "A la pantalla d'entrada, tria «He oblidat la contrasenya» i segueix "
                        "l'enllaç que t'arribarà al correu. El missatge de la pantalla és el "
                        "mateix tant si el correu té compte com si no."
                    ),
                },
                {
                    "id": "compte-doble-factor",
                    "q": _("Puc activar el doble factor?"),
                    "a": _(
                        "Sí. A «Seguretat del compte» pots activar el codi d'una aplicació "
                        "d'autenticació."
                    ),
                },
            ],
        },
        {
            "id": "tema-carnet",
            "roman": "II",
            "name": _("El carnet"),
            "questions": [
                {
                    "id": "carnet-on",
                    "q": _("On és el meu carnet digital?"),
                    "a": _("A «El meu carnet», des de l'inici de l'àrea del soci."),
                },
                {
                    "id": "carnet-sense-cobertura",
                    "q": _("Funciona sense cobertura?"),
                    "a": _("Pots desar-ne una còpia per ensenyar-la quan no tinguis connexió."),
                },
            ],
        },
        {
            "id": "tema-quotes",
            "roman": "III",
            "name": _("Quotes i pagaments"),
            "questions": [
                {
                    "id": "quotes-rebut",
                    "q": _("On trobo el rebut d'un pagament?"),
                    "a": _("A «Quotes», obre el pagament i tria «Rebut» per veure'l."),
                },
                {
                    "id": "quotes-dubtes",
                    "q": _("Tinc un dubte amb un pagament. A qui ho pregunto?"),
                    "a": _("Escriu a la secretaria del club des de l'adreça de contacte."),
                },
            ],
        },
    ],
}
