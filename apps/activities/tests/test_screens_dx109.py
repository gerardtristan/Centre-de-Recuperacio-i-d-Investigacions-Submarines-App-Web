"""T-DX-109 (Convite al 02): la fitxa pública d'una activitat té la capçalera de Convite (P-99 A):
el full de calendari amb el dia, el títol, les dades clau i els botons d'inscripció a
`convite-accions`. Les dades no canvien (`public.py`). Només dades inventades."""

import re

from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)

from .helpers import an_open_outing
from .test_public_pages import detail, manager, text  # noqa: F401 (fixture)


def test_the_public_detail_has_the_convite_header(client, manager):  # noqa: F811
    outing = an_open_outing(manager)
    page = main_of(text(client, detail(outing)))
    day = outing.starts_on.day
    assert re.search(rf'<b class="convite-dia">{day}</b>', page)
    assert 'class="convite-full" aria-hidden="true"' in page  # la data ja hi és en text
    actions = page.split('class="convite-accions"')[1].split("</div>")[0]
    assert "Inscriu-te com a soci" in actions and "boto-principal" in actions
