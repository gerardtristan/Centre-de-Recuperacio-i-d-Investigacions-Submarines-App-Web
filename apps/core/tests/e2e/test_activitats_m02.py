"""Catàlegs i activitats al navegador (T-M02-05 i T-M02-06; P-M02-A i P-M02-B): el responsable de
cursos i sortides afegeix un curs al catàleg i en canvia el preu, crea una sortida, hi posa el
programa i una sessió, la publica i la cancel·la amb motiu. Tot amb el teclat. Una secretària que
escriu l'adreça directament rep «no trobat».

Pantalles a 1280, 390 i 320 px, en clar i en fosc, amb l'auditoria automàtica d'accessibilitat
(axe i recorregut amb el teclat). No hi ha wireframe d'aquestes pantalles (T-M02-01): la revisió
visual és de la T-F1-01. Només dades inventades.
"""

import pytest
from django.conf import settings
from playwright.sync_api import expect

from apps.activities.models import Activity, TrainingCatalogueEntry
from apps.core.models import OutgoingEmail

from .conftest import login_admin, make_admin
from .test_accessibilitat_028 import audit, problems

pytestmark = pytest.mark.e2e

ADMIN = settings.ADMIN_URL_PATH
REASON = "Previsió de mala mar (motiu inventat)."


@pytest.fixture(autouse=True)
def _no_motion(page):
    page.emulate_media(reduced_motion="reduce")


@pytest.fixture
def manager(transactional_db):
    return make_admin("cursos.prova", "courses_manager")


def press(page, role, name, *, exact=True):
    """Activa un enllaç o un botó amb el teclat. `exact=False` per als enllaços que porten el nom
    de l'objecte en un text només per al lector de pantalla («Preus: nom de la fitxa»)."""
    page.get_by_role(role, name=name, exact=exact).first.focus()
    page.keyboard.press("Enter")


def test_manager_keeps_the_catalogue_and_changes_a_price(page, live_server, manager, review):
    make_admin("tresoreria.prova", "treasurer")
    login_admin(page, live_server.url, manager.login)
    accessibility = {}

    press(page, "link", "Catàleg de cursos")
    expect(page.get_by_role("heading", name="Catàleg de cursos")).to_be_visible()
    expect(page.get_by_text("Encara no hi ha cap fitxa en aquest catàleg.")).to_be_visible()
    review("cataleg-buit")

    press(page, "link", "Afegeix un curs al catàleg")
    expect(page.get_by_role("heading", name="Afegeix un curs al catàleg")).to_be_visible()
    # Sense dades, cada error surt al seu camp i no es desa res.
    press(page, "button", "Desa la fitxa")
    expect(page.get_by_text("Aquest camp és obligatori.").first).to_be_visible()
    review("fitxa-cataleg-errors")
    audit(page, "fitxa-cataleg", accessibility)
    assert not TrainingCatalogueEntry.objects.exists()

    page.get_by_label("Nom", exact=True).fill("Curs inventat de busseig")
    page.get_by_label("Places per defecte").fill("8")
    page.get_by_label("Preu de soci").fill("45")
    page.get_by_label("Preu de no soci").fill("60,50")
    page.get_by_label("Departament").select_option(label="General")
    press(page, "button", "Desa la fitxa")
    expect(page.get_by_text("Fitxa desada. Queda al registre d'activitat.")).to_be_visible()
    expect(page.get_by_role("rowheader", name="Curs inventat de busseig")).to_be_visible()
    review("cataleg-cursos")
    audit(page, "cataleg-cursos", accessibility)

    press(page, "link", "Preus", exact=False)
    expect(page.get_by_role("heading", name="Preus de «Curs inventat de busseig»")).to_be_visible()
    page.get_by_label("Preu de soci").fill("50")
    page.get_by_label("Motiu").fill("Puja el preu de soci (motiu inventat).")
    review("preus")
    audit(page, "preus", accessibility)
    press(page, "button", "Desa els preus")
    expect(page.get_by_text("Preus desats.")).to_be_visible()
    entry = TrainingCatalogueEntry.objects.get()
    assert entry.prices.count() == 2
    # El tresorer rep l'avís del canvi de preu (RN-AJ-04).
    assert OutgoingEmail.objects.filter(
        template="avis-canvi-diners", to_address="tresoreria.prova@example.org"
    ).exists()

    press(page, "link", "Tipus de sortida")
    expect(page.get_by_role("heading", name="Tipus de sortida")).to_be_visible()
    review("tipus-de-sortida")
    audit(page, "tipus-de-sortida", accessibility)

    press(page, "link", "Projectes de medi ambient")
    page.get_by_label("Nom del projecte").fill("Projecte inventat de neteja")
    page.get_by_label("Objectiu").fill("Objectiu inventat.")
    page.get_by_label("Departament").select_option(label="General")
    press(page, "button", "Crea el projecte")
    expect(page.get_by_text("Projecte creat.")).to_be_visible()
    review("projectes")
    audit(page, "projectes", accessibility)
    press(page, "link", "Fitxa", exact=False)
    expect(page.get_by_text("Aquest projecte encara no té cap sortida.")).to_be_visible()
    review("projecte")
    audit(page, "projecte", accessibility)

    assert not problems(accessibility), "; ".join(problems(accessibility))


def test_manager_creates_publishes_and_cancels_an_outing(page, live_server, manager, review):
    teacher = make_admin("instructora.prova", "instructor")
    login_admin(page, live_server.url, manager.login)
    accessibility = {}

    press(page, "link", "Activitats")
    expect(page.get_by_role("heading", name="Activitats")).to_be_visible()
    expect(page.get_by_text("Cap activitat coincideix amb els filtres.")).to_be_visible()
    review("activitats-buit")

    press(page, "link", "Sortida nova")
    expect(page.get_by_role("heading", name="Sortida nova")).to_be_visible()
    page.get_by_label("Tipus de sortida").select_option(label="Immersió")
    page.get_by_label("Títol").fill("Immersió inventada a les Medes")
    page.get_by_label("Data d'inici").fill("2027-06-14")
    page.get_by_label("Data de final").fill("2027-06-14")
    page.get_by_label("Data límit d'inscripció").fill("2027-06-10T20:00")
    page.get_by_label("Places").fill("12")
    page.get_by_label("Preu de soci").fill("45")
    review("sortida-nova")
    audit(page, "sortida-nova", accessibility)
    # Falta el preu de no soci: l'error surt al camp i no es crea res.
    press(page, "button", "Desa l'activitat")
    expect(page.get_by_text("Aquest camp és obligatori.")).to_be_visible()
    assert not Activity.objects.exists()
    page.get_by_label("Preu de no soci").fill("60")
    press(page, "button", "Desa l'activitat")
    expect(page.get_by_text("Activitat creada en esborrany.")).to_be_visible()
    expect(page.get_by_role("heading", name="Immersió inventada a les Medes")).to_be_visible()
    review("fitxa-esborrany")
    audit(page, "fitxa-esborrany", accessibility)
    outing = Activity.objects.get()

    press(page, "link", "Edita el programa")
    expect(page.get_by_role("heading", name="Programa del dia")).to_be_visible()
    first = page.get_by_role("group", name="Bloc 1")
    first.get_by_label("Hora d'inici").fill("08:00")
    first.get_by_label("Què s'hi fa").fill("Trobada al port")
    review("programa")
    audit(page, "programa", accessibility)
    press(page, "button", "Desa el programa")
    expect(page.get_by_text("Programa desat.")).to_be_visible()

    press(page, "link", "Afegeix una sessió")
    expect(page.get_by_role("heading", name="Afegeix una sessió")).to_be_visible()
    page.get_by_label("Classe de sessió").select_option(label="Mar")
    page.get_by_label("Comença").fill("2027-06-14T09:00")
    page.get_by_label("Acaba").fill("2027-06-14T11:00")
    page.get_by_label(str(teacher.person)).focus()
    page.keyboard.press("Space")
    review("sessio-nova")
    audit(page, "sessio-nova", accessibility)
    press(page, "button", "Desa la sessió")
    expect(page.get_by_text("Sessió desada.")).to_be_visible()
    assert list(outing.sessions.get().instructors.all()) == [teacher.person]

    press(page, "button", "Publica")
    expect(page.get_by_text("Activitat publicada: ja té les inscripcions obertes.")).to_be_visible()
    review("fitxa-oberta")
    audit(page, "fitxa-oberta", accessibility)
    outing.refresh_from_db()
    assert outing.status == Activity.Status.OPEN

    press(page, "link", "Activitats")
    expect(page.get_by_role("rowheader", name="Immersió inventada a les Medes")).to_be_visible()
    review("activitats")
    audit(page, "activitats", accessibility)

    press(page, "link", "Fitxa", exact=False)
    press(page, "link", "Cancel·la l'activitat…")
    expect(page.get_by_role("heading", name="Cancel·la l'activitat")).to_be_visible()
    press(page, "button", "Cancel·la l'activitat")
    expect(page.get_by_text("Cal escriure el motiu de la cancel·lació.")).to_be_visible()
    review("cancella-errors")
    audit(page, "cancella", accessibility)
    page.get_by_label("Motiu").fill(REASON)
    press(page, "button", "Cancel·la l'activitat")
    expect(page.get_by_text("Activitat cancel·lada.")).to_be_visible()
    expect(page.get_by_text(REASON)).to_be_visible()
    review("fitxa-cancellada")
    outing.refresh_from_db()
    assert (outing.status, outing.cancellation_reason) == (Activity.Status.CANCELLED, REASON)

    assert not problems(accessibility), "; ".join(problems(accessibility))


def test_someone_without_the_permission_gets_not_found_by_typing_the_address(
    page, live_server, manager, page_checks
):
    """Accés directe: la secretària no té ni el catàleg (AC6) ni les activitats (AC7). El menú
    no li ensenya cap enllaç i, si escriu l'adreça, rep «no trobat»."""
    secretary = make_admin("secretaria.m02", "secretary")
    login_admin(page, live_server.url, secretary.login)
    expect(page.get_by_role("link", name="Activitats", exact=True)).to_have_count(0)
    expect(page.get_by_role("link", name="Catàleg de cursos", exact=True)).to_have_count(0)
    for path in (
        f"/{ADMIN}/activitats/",
        f"/{ADMIN}/activitats/sortida/nova/",
        f"/{ADMIN}/cataleg/cursos/",
        f"/{ADMIN}/sortides/tipus/",
    ):
        page_checks.expect(404, path)
        response = page.goto(f"{live_server.url}{path}")
        assert response.status == 404, path
        expect(page.get_by_role("heading", level=1)).not_to_contain_text("Activitats")


def test_a_visitor_sees_what_is_published_and_the_manager_duplicates_it(
    page, live_server, manager, review, page_checks
):
    """T-M02-08 i T-M02-07: sense entrar, un visitant veu el llistat i el detall d'una activitat
    publicada (i «no trobat» si és un esborrany, CA-M02-05). Després el responsable la duplica."""
    from apps.activities import states
    from apps.activities.tests.helpers import an_outing

    outing = an_outing(manager, title="Immersió inventada publicada", location="Port inventat")
    states.publish(outing, by=manager)
    draft = an_outing(manager, title="Esborrany inventat que no s'ha de veure")
    accessibility = {}

    page.goto(f"{live_server.url}/activitats/")
    expect(page.get_by_role("heading", name="Cursos i sortides")).to_be_visible()
    expect(page.get_by_role("link", name="Immersió inventada publicada")).to_be_visible()
    expect(page.get_by_text("Esborrany inventat")).to_have_count(0)
    review("public-llistat")
    audit(page, "public-llistat", accessibility)

    press(page, "link", "Immersió inventada publicada")
    expect(page.get_by_role("heading", name="Immersió inventada publicada")).to_be_visible()
    expect(page.get_by_text("Inscripcions obertes")).to_be_visible()
    expect(page.get_by_text("Només socis del club")).to_be_visible()
    review("public-detall")
    audit(page, "public-detall", accessibility)

    page_checks.expect(404, f"/activitats/{draft.pk}/")
    response = page.goto(f"{live_server.url}/activitats/{draft.pk}/")
    assert response.status == 404

    login_admin(page, live_server.url, manager.login)
    page.goto(f"{live_server.url}/{ADMIN}/activitats/{outing.pk}/")
    press(page, "link", "Duplica…")
    expect(page.get_by_role("heading", name="Duplica l'activitat")).to_be_visible()
    page.get_by_label("Data d'inici de la còpia").fill("2028-06-13")
    review("duplica")
    audit(page, "duplica", accessibility)
    press(page, "button", "Crea la còpia")
    expect(page.get_by_text("Còpia creada en esborrany.")).to_be_visible()
    expect(page.get_by_text("Duplicada de")).to_be_visible()
    review("fitxa-copia")
    copy = Activity.objects.get(duplicated_from=outing)
    assert (copy.status, str(copy.starts_on)) == (Activity.Status.DRAFT, "2028-06-13")

    assert not problems(accessibility), "; ".join(problems(accessibility))
