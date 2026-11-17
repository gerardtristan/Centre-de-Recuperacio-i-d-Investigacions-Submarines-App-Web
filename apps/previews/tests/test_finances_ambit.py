"""T-DX-33: el format dels imports de l'exemple (català) i que els totals quadren."""

from apps.previews.screens.finances_ambit import AREAS, CONTEXT, eur


def test_amounts_use_the_catalan_format():
    assert eur(123456) == "1.234,56 €"
    assert eur(-12000, sign=True) == "−120,00 €"
    assert eur(488000, sign=True) == "+4.880,00 €"


def test_the_example_totals_add_up():
    income = sum(i for _n, i, _o in AREAS)
    expense = sum(o for _n, _i, o in AREAS)
    assert CONTEXT["total_result"] == eur(income - expense, sign=True) == "+6.013,75 €"
