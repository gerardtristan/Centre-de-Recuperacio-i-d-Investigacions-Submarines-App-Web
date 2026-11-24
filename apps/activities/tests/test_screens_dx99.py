"""T-DX-99 (revisió de DISSENY de la #526): a la fitxa d'una activitat, «Cancel·la l'activitat»
(rar i que no es desfà) va plegat dins d'un `details`, com «Duplica l'activitat», i els botons
d'estat d'un sol clic van en una sola fila d'accions. Només dades inventades."""

import re

from apps.accounts.security import AREA_ADMIN
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)

from .helpers import an_open_outing
from .test_admin_states import detail, manager  # noqa: F401 (fixture)


def test_cancel_is_folded_and_state_buttons_share_a_row(login_as, manager):  # noqa: F811
    outing = an_open_outing(manager)
    page = main_of(login_as(manager, AREA_ADMIN).get(detail(outing)).content.decode())
    pattern = r"<details>\s*<summary>Cancel·la l'activitat…</summary>(.*?)</details>"
    folded = re.search(pattern, page, re.S)
    assert folded and 'value="cancella"' in folded.group(1)
    rows = re.findall(r'<div class="accions">(.*?)</div>', page, re.S)
    assert any(row.count('name="accio"') >= 2 for row in rows)
