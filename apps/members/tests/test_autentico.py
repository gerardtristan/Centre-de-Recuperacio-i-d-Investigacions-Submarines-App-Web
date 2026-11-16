"""Autentico (T-DX-15): el segell de la verificació del carnet diu el mateix que el resultat del
servidor (RN-M01-26) i no apareix quan la verificació està bloquejada."""

import pytest

from apps.members.tests.test_card_verify import (
    INVENTED,
    LIMIT,
    card_for,
    main,
    no_padding,  # noqa: F401 (fixture autouse)
    url,
)
from apps.members.tests.test_cards import paid_member


def seal(html):
    return (
        html.split('class="autentico-segell"', 1)[1].split("</p>", 1)[0]
        if "autentico-segell" in html
        else None
    )


@pytest.mark.django_db
def test_a_valid_card_gets_the_valid_seal(client):
    html = main(client.get(url(card_for(paid_member()))))
    assert "autentico-valid" in html and "Vàlid" in seal(html) and "No vàlid" not in seal(html)


@pytest.mark.django_db
def test_an_unknown_card_gets_the_not_valid_seal(client):
    html = main(client.get(url(INVENTED)))
    assert "autentico-no-valid" in html and "No vàlid" in seal(html)


@pytest.mark.django_db
def test_a_blocked_check_has_no_seal(client):
    for _ in range(LIMIT):
        client.get(url(INVENTED))
    html = main(client.get(url(INVENTED)))
    assert seal(html) is None
