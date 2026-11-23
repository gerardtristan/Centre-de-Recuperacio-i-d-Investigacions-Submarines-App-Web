"""T-DX-92 (revisió de DISSENY de «Cursos i sortides», #465): al llistat, el botó «Fitxa» porta
`enllac-fila`, perquè tota la fila porti a la fitxa de l'activitat (B14), com al llistat de socis.
Només dades inventades."""

from django.urls import reverse

from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)

from .helpers import an_outing
from .test_admin_activities import LIST, client_of, manager  # noqa: F401 (fixture)


def test_the_whole_row_opens_the_activity(client_of, manager):  # noqa: F811
    activity = an_outing(manager)
    html = main_of(client_of(manager).get(LIST).content.decode())
    url = reverse("administration:activity_detail", args=[activity.pk])
    assert f'<a class="boto boto-petit enllac-fila" href="{url}">' in html
