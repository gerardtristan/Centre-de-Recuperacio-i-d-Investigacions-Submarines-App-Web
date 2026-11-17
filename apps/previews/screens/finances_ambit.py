"""T-DX-33 Gastos: ingressos, despeses i resultat per àmbit (centre de cost; mòdul 09).

Contingut d'exemple, inventat: la llista de departaments encara no és fixada (Q-17), i els que no
són «General» són d'exemple. Els imports són en cèntims i aquí només es formaten.
"""

from django.utils.translation import gettext_lazy as _

TITLE = _("Finances per àmbit")

# (àmbit, ingressos, despeses), en cèntims
AREAS = [
    (_("General"), 612000, 124000),
    (_("Escola de busseig (exemple)"), 145000, 86050),
    (_("Sortides (exemple)"), 298000, 231575),
    (_("Departament d'Història"), 0, 12000),
]


def eur(cents, sign=False):
    """Format català: «1.234,56 €»; amb `sign`, «+» o «−» davant."""
    text = f"{abs(cents) / 100:,.2f}".replace(",", " ").replace(".", ",").replace(" ", ".")
    prefix = ("−" if cents < 0 else "+") if sign else ("−" if cents < 0 else "")
    return f"{prefix}{text} €"


def _context():
    total_in = sum(i for _n, i, _o in AREAS)
    total_out = sum(o for _n, _i, o in AREAS)
    rows, start = [], 0.0
    for index, (name, cents_in, cents_out) in enumerate(AREAS, start=1):
        share = cents_out * 100 / total_out
        rows.append(
            {
                "name": name,
                "income": eur(cents_in),
                "expense": eur(cents_out),
                "result": eur(cents_in - cents_out, sign=True),
                "negative": cents_in < cents_out,
                "share": f"{share:.0f}",
                # Segment de l'anell sobre pathLength=100, amb un petit buit entre segments
                "dash": f"{max(share - 1, 0.5):.2f} 100",
                "offset": f"{-start:.2f}",
                "segment": index,
            }
        )
        start += share
    return {
        "month": _("Octubre 2026 (exemple)"),
        "rows": rows,
        "total_in": eur(total_in),
        "total_out": eur(total_out),
        "total_result": eur(total_in - total_out, sign=True),
    }


CONTEXT = _context()
