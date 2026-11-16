"""T-DX-40 Seguir i Monograma: la part social i els avatars. Contingut d'exemple, inventat."""

from django.utils.translation import gettext_lazy as _

TITLE = _("Social")
CONTEXT = {
    # Llavors d'exemple per a l'avatar (Monograma, T-DX-18): mai el nom ni cap dada de la persona
    "my_seed": "exemple-social-0",
    "variants": [
        "exemple-variant-1",
        "exemple-variant-2",
        "exemple-variant-3",
        "exemple-variant-4",
    ],
    # Socis d'exemple (només un nom inventat) i un recompte de seguidors
    "people": [
        {"name": "Laia", "seed": "exemple-social-1", "followers": 12, "following": True},
        {"name": "Pau", "seed": "exemple-social-2", "followers": 7, "following": False},
        {"name": "Nil", "seed": "exemple-social-3", "followers": 3, "following": False},
    ],
}
