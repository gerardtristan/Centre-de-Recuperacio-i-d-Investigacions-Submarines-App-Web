"""T-DX-90 (revisió de DISSENY de les pantalles del 09): els desplegables de «Registra una despesa»
diuen què cal triar, en català, i no «---------»; l'import de «Despeses sense factura» va alineat a
la dreta (`cel-import`, regla D14). Només dades inventades."""

from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)

from .test_views import R, as_role  # noqa: F401 (fixture)


def test_the_new_expense_selects_say_what_to_choose(as_role):  # noqa: F811
    html = main_of(as_role(R.TREASURER).get(reverse("administration:expense_new")).content.decode())
    assert "---------" not in html
    for text in ("Tria un proveïdor", "Tria una categoria", "Tria un departament"):
        assert text in html


def test_the_amount_column_is_right_aligned(login_as, make_admin):  # noqa: F811
    client = login_as(make_admin(R.TREASURER), AREA_ADMIN)
    html = main_of(client.get(reverse("administration:expenses_without_invoice")).content.decode())
    assert '<th scope="col" class="cel-import">Import</th>' in html


def test_a_select_with_an_error_is_marked_invalid(as_role):  # noqa: F811
    # La vora vermella dels camps amb error (comptes.css) també val per als desplegables.
    client = as_role(R.TREASURER)
    html = client.post(
        reverse("administration:expense_new"), {"invoice_number": ""}
    ).content.decode()
    assert 'aria-invalid="true"' in html.split('<select name="supplier"')[1].split(">")[0]
