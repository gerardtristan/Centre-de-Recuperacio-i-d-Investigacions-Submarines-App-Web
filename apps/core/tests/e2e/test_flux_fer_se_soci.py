"""El flux sencer «fer-se soci» al navegador, de la sol·licitud al carnet verificat (llesca 1 del
pla d'acceleració, `docs/plans/pla-acceleracio.md` §3; processos P-M01-A i P-M01-E del pla).

Cada tram es fa a la pantalla real i amb el rol que toca:

1. Visitant: omple «Fer-se soci» a la web (CA-M01-01).
2. Secretaria, amb doble factor: aprova l'alta; el soci queda pendent, amb número, quota i
   invitació (CA-M01-03).
3. La persona: crea el compte amb la invitació, veu la quota pendent i encara no té carnet.
4. Tresoreria, amb doble factor: veu la quota pendent i **registra el pagament a mà, amb motiu**.
5. Tresoreria: veu el soci actiu, amb la quota pagada i el carnet emès (CA-M01-06).
6. El soci: veu la quota pagada i el carnet amb el codi QR (CA-M01-12).
7. Qualsevol, sense sessió: la verificació pública diu «Vàlid», el número i el nom de pila, i
   res més (CA-M01-13).

**Tram que falta: el registre manual del pagament (pas 4).** No té pantalla ni servei: està
bloquejat per P-12 (`docs/decisions/pendents.md`; RN-72 de la 00; `charges.mark_paid` rebutja
l'origen «manual»). Per això hi ha dues proves amb els mateixos trams:

- la del flux encadenat sencer, que busca el registre manual a la fitxa del soci i avui no el
  troba: `xfail` estricte amb la referència a P-12. Només s'accepta que falli per aquest tram
  (`raises=MissingStep`); si es trenca qualsevol altre, falla de debò;
- la que passa: fa tots els altres trams al navegador i salta aquest amb els serveis que el
  proveïdor de pagaments cridarà (`charges.mark_paid` i `services.on_fee_paid`, amb
  `_Builder.pay`), sense SQL.

Quan existeixi la pantalla de la P-12, cal adaptar `register_manual_payment_on_screen`, treure
l'`xfail` i esborrar la prova que salta el tram.

Només dades inventades. Les dates que es comparen amb la pantalla surten de l'hora local del
pagament desat, no de l'hora en què s'executa la prova.
"""

import re

import pytest
from django.conf import settings
from django.utils import timezone
from playwright.sync_api import expect

from apps.accounts.models import Account
from apps.core import charges
from apps.core.models import Charge, OutgoingEmail, Payment
from apps.members import cards, validity
from apps.members.models import Member, MemberCard, MemberRequest, MembershipNumberCounter
from conftest import PASSWORD

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e

ADMIN = settings.ADMIN_URL_PATH

FIRST_NAME = "Mar"
LAST_NAME = "Sirena Inventada"
FULL_NAME = f"{FIRST_NAME} {LAST_NAME}"
EMAIL = "mar.sirena@example.org"

P12 = (
    "P-12 (docs/decisions/pendents.md; RN-72 de la 00): el registre manual del pagament no té "
    "pantalla ni servei. És l'únic tram que falta del flux «fer-se soci»."
)
# Com es dirà, previsiblement, l'acció de la pantalla que falta (fitxa del soci, tresoreria).
MANUAL_PAYMENT = re.compile(r"Registra\w* (el |un |)(pagament|cobrament)", re.IGNORECASE)


class MissingStep(AssertionError):
    """El flux s'atura en un tram que encara no té pantalla."""


def detail(page, term):
    """El valor d'una dada de la pantalla (`dd`), pel nom que la presenta (`dt`)."""
    row = page.locator("dl.dades-soci > div").filter(has=page.get_by_text(term, exact=True))
    return row.locator("dd").first


def day(moment):
    """La data local (Barcelona) d'un instant desat, tal com la mostra la pantalla."""
    return timezone.localtime(moment).date()


def login_personal(page, base_url):
    page.goto(f"{base_url}/entrar/")
    page.get_by_label("Correu electrònic").fill(EMAIL)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    expect(page.get_by_role("button", name="Surt")).to_be_visible()


# --- Tram 4: el pagament de la quota, de dues maneres ------------------------------------------
def register_manual_payment_on_screen(page, builder, fee):
    """El tresorer registra el pagament a mà, amb motiu, des de la fitxa del soci. Avui l'acció
    no hi és (P-12): la pàgina ja és carregada i sencera, i es mira sense esperar."""
    action = page.get_by_text(MANUAL_PAYMENT)
    if action.count() == 0:
        raise MissingStep(P12)
    # A partir d'aquí, una suposició del que tindrà la pantalla: qui la construeixi l'ajusta.
    action.first.click()
    page.get_by_label("Motiu").fill("Paga en efectiu a la secretaria (prova inventada)")
    page.get_by_role("button", name=MANUAL_PAYMENT).click()


def confirm_payment_with_the_service(page, builder, fee):
    """Salta el tram que falta: el pagament el confirmen els serveis de la 00 i del 01, com ho
    farà la notificació verificada del proveïdor. Cap pantalla i cap SQL."""
    builder.pay(fee)


# --- El flux ------------------------------------------------------------------------------------
def join_flow(page, base_url, builder, secretary, pay, shoot=lambda name: None):
    full = builder.full
    amount = charges.euros(full.annual_fee_cents)
    last_number = MembershipNumberCounter.objects.get(pk=1).last_number

    # 1. Visitant: «Fer-se soci» a la web. La data torna a dibuixar la part del formulari que en
    # depèn (HTMX): s'espera l'etiqueta del document d'un major d'edat abans de continuar.
    page.goto(f"{base_url}/fer-se-soci/")
    expect(page.get_by_role("heading", name="Sol·licitud d'alta")).to_be_visible()
    page.get_by_label("Nom", exact=True).fill(FIRST_NAME)
    page.get_by_label("Cognoms", exact=True).fill(LAST_NAME)
    page.get_by_label("Data de naixement").fill("1990-05-20")
    expect(page.locator("#etiqueta-document")).to_have_text("Document d'identitat (DNI o NIE)")
    page.get_by_label("Document d'identitat (DNI o NIE)", exact=True).fill("12345678Z")
    page.get_by_label("Correu electrònic", exact=True).fill(EMAIL)
    page.get_by_label("Telèfon", exact=True).fill("600 000 002")
    # El botó d'opció és amagat a la vista: es tria amb la seva etiqueta, com fa una persona.
    page.locator("label", has=page.get_by_role("radio")).filter(has_text=full.name).click()
    expect(page.get_by_role("radio", name=re.compile(re.escape(full.name)))).to_be_checked()
    page.get_by_role("checkbox", name=re.compile("Política de privacitat")).check()
    page.get_by_role("checkbox", name=re.compile("Condicions de soci")).check()
    shoot("1-formulari-omplert")
    page.get_by_role("button", name="Envia la sol·licitud").click()
    expect(page.get_by_text("Sol·licitud enviada")).to_be_visible()
    expect(page.get_by_text("Encara no és una alta")).to_be_visible()
    shoot("1-sollicitud-enviada")
    join = MemberRequest.objects.get(kind=MemberRequest.Kind.JOIN, person__contact_email=EMAIL)
    assert join.status == MemberRequest.Status.PENDING
    assert join.channel == MemberRequest.Channel.WEB
    assert not Member.objects.filter(person=join.person).exists()  # encara no és cap soci
    assert OutgoingEmail.objects.filter(template="rebut-sollicitud-alta", to_address=EMAIL).exists()

    # 2. Secretaria (doble factor): aprova l'alta. Número, quota del tipus i invitació.
    login_admin(page, base_url, secretary.login)
    page.goto(f"{base_url}/{ADMIN}/socis/altes/")
    expect(page.get_by_role("heading", name=re.compile(FULL_NAME))).to_be_visible()
    shoot("2-altes-pendents")
    page.get_by_role("button", name="Aprova l'alta").click()
    expect(page.get_by_text("Se li ha enviat el correu d'accés")).to_be_visible()
    member = Member.objects.get(person=join.person)
    assert member.member_number == last_number + 1
    fee = member.fees.get()
    assert fee.charge.status == Charge.Status.PENDING
    assert fee.charge.amount_cents == full.annual_fee_cents
    page.goto(f"{base_url}/{ADMIN}/socis/{member.pk}/")
    expect(page.get_by_role("heading", level=1, name=FULL_NAME)).to_be_visible()
    expect(detail(page, "Número")).to_have_text(str(member.member_number))
    expect(detail(page, "Estat del soci")).to_contain_text("Pendent")
    # L'estat de cada quota és el del seu càrrec. L'estat general de la quota no diu res d'una
    # quota pendent que encara no ha vençut (079, RN-M01-86): aquí no es comprova.
    fee_row = page.get_by_role("row", name=re.compile(re.escape(fee.charge.concept)))
    expect(fee_row).to_contain_text(amount)
    expect(fee_row).to_contain_text("Pendent")
    expect(page.get_by_text("Ara no té cap carnet vigent.")).to_be_visible()
    shoot("2-fitxa-soci-pendent")
    page.context.clear_cookies()  # la persona obre el correu en un altre navegador

    # 3. La persona: crea el compte amb la invitació, veu la quota pendent i cap carnet.
    invitation = OutgoingEmail.objects.get(template="invitacio-compte", to_address=EMAIL)
    token = re.search(r"http\S+/compte/invitacio/(\S+)", invitation.body_text).group(1)
    page.goto(f"{base_url}/compte/invitacio/{token}")
    expect(page.get_by_role("heading", name="Crear el compte")).to_be_visible()
    page.get_by_label("Contrasenya nova").fill(PASSWORD)
    page.get_by_label("Torna-la a escriure").fill(PASSWORD)
    page.get_by_role("button", name="Crear el compte").click()
    expect(page.get_by_text("Compte creat")).to_be_visible()
    assert Account.objects.get(person=join.person).status == Account.Status.ACTIVE
    login_personal(page, base_url)
    account_nav = page.get_by_role("navigation", name="Compte personal")
    account_nav.get_by_role("link", name="Les meves quotes").click()
    expect(page.get_by_role("heading", name="Les meves quotes")).to_be_visible()
    expect(fee_row).to_contain_text(amount)
    expect(fee_row).to_contain_text("Pendent")
    shoot("3-quota-pendent")
    account_nav.get_by_role("link", name="El meu carnet").click()
    expect(page.get_by_text("Ara no tens cap carnet.")).to_be_visible()
    expect(page.get_by_role("button", name="Demana un carnet nou")).to_be_hidden()
    shoot("3-sense-carnet")
    page.get_by_role("button", name="Surt").click()
    expect(page.get_by_role("button", name="Entrar")).to_be_visible()

    # 4. Tresoreria (doble factor): veu la quota pendent a la fitxa i registra el pagament.
    treasurer = make_admin("tresoreria.prova", "treasurer")
    login_admin(page, base_url, treasurer.login)
    page.goto(f"{base_url}/{ADMIN}/socis/{member.pk}/")
    expect(page.get_by_text("Vista de tresoreria: dades mínimes.")).to_be_visible()
    expect(fee_row).to_contain_text(amount)
    expect(fee_row).to_contain_text("Pendent")
    shoot("4-tresoreria-quota-pendent")
    pay(page, builder, fee)

    # 5. Tresoreria: el soci és actiu, la quota és pagada fins d'aquí a 12 mesos i té carnet.
    paid_on = day(Payment.objects.get(charge=fee.charge).paid_at)
    until = validity.twelve_months_after(paid_on)
    page.goto(f"{base_url}/{ADMIN}/socis/{member.pk}/")
    expect(detail(page, "Estat del soci")).to_contain_text("Actiu")
    expect(detail(page, "Quota")).to_contain_text(f"Pagada fins al {until:%d/%m/%Y}")
    expect(page.get_by_text("Ara no té cap carnet vigent.")).to_be_hidden()
    expect(page.get_by_text(re.compile(r"^Emès el \d"))).to_be_visible()
    shoot("5-fitxa-soci-actiu")
    page.goto(f"{base_url}/{ADMIN}/quotes/")
    expect(page.get_by_role("heading", name="Quotes i impagats")).to_be_visible()
    review_row = page.get_by_role("row", name=re.compile(FULL_NAME))
    expect(review_row).to_contain_text(f"Soci {member.member_number}")
    expect(review_row).to_contain_text(f"Pagada fins al {until:%d/%m/%Y}")
    shoot("5-quotes-i-impagats")
    page.context.clear_cookies()

    # 6. El soci: la quota surt pagada i ja té el carnet, vàlid i amb el codi QR.
    login_personal(page, base_url)
    account_nav.get_by_role("link", name="Les meves quotes").click()
    expect(detail(page, "Estat de la quota")).to_contain_text(f"Pagada fins al {until:%d/%m/%Y}")
    expect(fee_row).to_contain_text(f"Pagada el {paid_on:%d/%m/%Y}")
    shoot("6-quota-pagada")
    account_nav.get_by_role("link", name="El meu carnet").click()
    expect(page.get_by_role("heading", name="El meu carnet")).to_be_visible()
    expect(detail(page, "Número de soci")).to_have_text(str(member.member_number))
    expect(detail(page, "Estat del carnet")).to_contain_text("Vàlid")
    expect(detail(page, "Estat del carnet")).not_to_contain_text("No vàlid")
    expect(detail(page, "Vàlid fins al")).to_have_text(f"{until:%d/%m/%Y}")
    expect(page.get_by_role("img", name="Codi QR per verificar el carnet")).to_be_visible()
    shoot("6-carnet")
    page.context.clear_cookies()  # qui escaneja el QR no té cap sessió

    # 7. Verificació pública: l'adreça que porta el QR diu «Vàlid», el número i el nom de pila.
    card = MemberCard.objects.get(member=member, revoked_at__isnull=True)
    public_path = cards.verification_url(cards.qr_token(card)).split(settings.PUBLIC_SITE_URL)[1]
    page.goto(f"{base_url}{public_path}")
    expect(page.get_by_role("heading", name="Vàlid", exact=True)).to_be_visible()
    expect(detail(page, "Número de soci")).to_have_text(str(member.member_number))
    expect(detail(page, "Nom")).to_have_text(FIRST_NAME)
    expect(page.get_by_text(LAST_NAME)).to_have_count(0)  # cap altra dada (CA-M01-13)
    expect(page.get_by_text(EMAIL)).to_have_count(0)
    shoot("7-verificacio-valida")
    assert Member.objects.get(pk=member.pk).status == Member.Status.ACTIVE


def test_ca_m01_01_03_06_12_13_join_flow_from_the_request_to_the_verified_card(
    page, live_server, builder, secretary, capture
):
    """Tots els trams que existeixen, al navegador; el pagament (P-12), pels serveis."""
    join_flow(page, live_server.url, builder, secretary, confirm_payment_with_the_service, capture)


@pytest.mark.xfail(strict=True, raises=MissingStep, reason=P12)
def test_ca_m01_01_03_06_12_13_join_flow_with_the_manual_payment_on_screen(
    page, live_server, builder, secretary
):
    """El flux encadenat sencer, també amb el registre manual del pagament a la pantalla."""
    join_flow(page, live_server.url, builder, secretary, register_manual_payment_on_screen)
