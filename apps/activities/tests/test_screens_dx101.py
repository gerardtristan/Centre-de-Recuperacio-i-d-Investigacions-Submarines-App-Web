"""T-DX-101 (revisió de DISSENY de la #536): a la taula de sessions de la fitxa, cancel·lar una
sessió (rar i no es desfà) va plegat en un `details` a la cel·la d'accions, amb l'etiqueta del motiu
visible, com «Cancel·la l'activitat…» (T-DX-99). Només dades inventades."""

import re

from apps.accounts.security import AREA_ADMIN
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)

from .helpers import a_place, an_open_course
from .test_admin_schedule import detail, manager, session_post  # noqa: F401 (fixture)


def test_cancelling_a_session_is_folded_with_a_visible_label(login_as, manager):  # noqa: F811
    course = an_open_course(manager)
    client = login_as(manager, AREA_ADMIN)
    client.post(detail(course), session_post(a_place(manager)))
    page = main_of(client.get(detail(course)).content.decode())
    cell = re.search(r'<td class="cel-accions">(.*?)</td>', page, re.S).group(1)
    assert "<details>" in cell and "<summary>Cancel·la…" in cell
    assert 'class="visualment-amagat" for="motiu-sessio-' not in cell
    assert 'name="cancel_sessio"' in cell.split("</summary>")[1]
