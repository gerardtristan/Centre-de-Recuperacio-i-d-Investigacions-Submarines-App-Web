"""Permisos del 01 per cel·la: rutes, objecte propi i serveis (T-M01-37; CA-RP-13; 059).

- Cada ruta del 01 × cada rol de la configuració inicial (i el compte personal sense rol): el que
  s'espera surt de la matriu carregada a la base de dades (`has_perm`), mai d'una taula escrita
  aquí, i del permís que `apps/members/permissions.py` declara per a la ruta.
- Una ruta nova del 01 sense declaració fa fallar la prova.
- Els serveis principals rebutgen amb «no trobat» un compte sense el permís, també cridats fora de
  la vista; amb el permís, la comprovació no els atura.

Només dades inventades.
"""

import datetime
import time
from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.test import Client
from django.urls import reverse

from apps.accounts.models import Account
from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY
from apps.core import audit
from apps.core.models import AuditEntry, Charge, Person, Role
from apps.core.permissions import has_perm
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_access import PUBLIC_ROUTES, _routes
from apps.members import (
    admissions,
    cards,
    fees,
    join,
    licences,
    member_edit,
    member_requests,
    services,
)
from apps.members.fee_rules import local_today
from apps.members.models import LicenceRecord, Member, MemberRequest, MembershipType
from apps.members.permissions import ACTIONS, OWN, PUBLIC, ROUTES
from conftest import PASSWORD

ROLES = [code for code in Role.Code.values if code not in ("member", "visitor", "guest")]
PERSONAL = "personal"  # el compte personal, que no hereta cap rol (059, punt 4.2)
ACCOUNTS = [*ROLES, PERSONAL]
REASON = "Motiu inventat de proves"
MODULE_ROUTES = {
    name: kwargs for name, view, kwargs in _routes() if view.__module__.startswith("apps.members.")
}
ADMIN_ROUTES = sorted(name for name, need in ROUTES.items() if isinstance(need, dict))
OWN_ROUTES = sorted(name for name, need in ROUTES.items() if need == OWN)

# Quin objecte va a cada paràmetre de la ruta: per defecte, pel nom del paràmetre.
OBJECT_FOR_PARAM = {
    "pk": "other",
    "record_pk": "record",
    "record_id": "own_record",
    "fee_id": "own_fee",
    "fee_pk": "fee",  # T-M01-40: una quota del soci «other»
}
OBJECT_FOR_ROUTE = {
    "administration:join_approve": "join_request",
    "administration:join_reject": "join_request",
    "administration:member_request_detail": "leave",
    "administration:fee_payment_reviewed": "fee",  # 079 (A-17): el paràmetre és una quota
}
_numbers = iter(range(500, 10_000))


def a_member(first, *, type_code="supporter"):
    person = Person.objects.create(
        first_name=first,
        last_name="Prova",
        origin=Person.Origin.WEB,
        contact_email=f"{first.lower()}@example.org",
    )
    return Member.objects.create(
        person=person,
        member_number=next(_numbers),
        type=MembershipType.objects.get(code=type_code),
        status=Member.Status.ACTIVE,
        joined_on=datetime.date(2019, 3, 12),
    )


def a_record(member):
    return LicenceRecord.objects.create(
        member=member,
        licence_type="Anual FECDAS",
        issued_on=datetime.date(2026, 1, 15),
        source=LicenceRecord.Source.CLUBER,  # caducitat desconeguda: també la confirmació en bloc
    )


@pytest.fixture
def world(make_admin):  # noqa: F811
    """Un soci d'una altra persona amb llicència, baixa pendent i quota; un altre amb el
    suplement vençut d'un canvi aprovat; una alta pendent; i el soci del compte personal."""
    issuer = make_admin()  # autor dels càrrecs de la preparació, sense cap rol
    other = a_member("Altra")
    changer = a_member("Canvi")
    supplement = fees.issue_type_change_supplement(
        changer,
        MembershipType.objects.get(code=member_requests.FULL),
        period=2026,
        due_on=datetime.date(2026, 1, 1),
        by=issuer,
    )
    own = a_member("Propia")
    personal = Account.objects.create_personal(own.person, own.person.contact_email, PASSWORD)
    personal.status = Account.Status.ACTIVE
    personal.save()
    applicant = Person.objects.create(
        first_name="Sollicitant",
        last_name="Prova",
        origin=Person.Origin.WEB,
        contact_email="sollicitant@example.org",
        id_document_type="dni",
        id_document_number="12345678Z",
    )
    return SimpleNamespace(
        other=other,
        record=a_record(other),
        fee=fees.issue_annual_fee(other, period=2026, due_on=datetime.date(2026, 3, 1), by=issuer),
        leave=MemberRequest.objects.create(
            kind=MemberRequest.Kind.LEAVE,
            person=other.person,
            member=other,
            request_reason=REASON,
            channel=MemberRequest.Channel.WEB,
        ),
        change=MemberRequest.objects.create(
            kind=MemberRequest.Kind.CHANGE_TYPE,
            person=changer.person,
            member=changer,
            requested_type=MembershipType.objects.get(code=member_requests.FULL),
            channel=MemberRequest.Channel.WEB,
            status=MemberRequest.Status.APPROVED,
            supplement_fee=supplement,
        ),
        join_request=MemberRequest.objects.create(
            kind=MemberRequest.Kind.JOIN,
            person=applicant,
            requested_type=MembershipType.objects.get(code="supporter"),
            channel=MemberRequest.Channel.WEB,
            birth_date=datetime.date(1990, 2, 14),
        ),
        own=own,
        own_record=a_record(own),
        own_fee=fees.issue_annual_fee(
            own, period=2026, due_on=datetime.date(2026, 3, 1), by=issuer
        ),
        personal=personal,
    )


def account_for(make_admin, world, who):  # noqa: F811
    return world.personal if who == PERSONAL else make_admin(who)


def client_for(account):
    client = Client()
    client.force_login(account)
    session = client.session
    session[AREA_SESSION_KEY] = (
        AREA_PERSONAL if account.kind == Account.Kind.PERSONAL else AREA_ADMIN
    )
    session[AUTH_AT_SESSION_KEY] = time.time()
    session.save()
    return client


def url_for(name, world):
    kwargs = {
        param: getattr(world, OBJECT_FOR_ROUTE.get(name) or OBJECT_FOR_PARAM[param]).pk
        for param in MODULE_ROUTES[name]
    }
    return reverse(name, kwargs=kwargs)


def is_login_redirect(response, login_name):
    return response.status_code == 302 and response["Location"].startswith(reverse(login_name))


# --- Declaració -----------------------------------------------------------------------------


def test_every_route_of_the_module_declares_its_permission():
    # Una ruta nova del 01 sense declaració (ni permís, ni pròpia, ni pública) fa fallar això.
    assert set(MODULE_ROUTES) == set(ROUTES)


def test_declared_public_routes_are_the_public_ones():
    public = {name for name, need in ROUTES.items() if need == PUBLIC}
    assert public == {name for name in PUBLIC_ROUTES if name in MODULE_ROUTES}


def test_every_admin_route_declares_get_and_post():
    for name in ADMIN_ROUTES:
        assert set(ROUTES[name]) == {"GET", "POST"}, name
        assert name.startswith("administration:"), name


# --- CA-RP-13: ruta × rol, a partir de la matriu carregada ------------------------------------


@pytest.mark.parametrize("who", ACCOUNTS)
@pytest.mark.parametrize("name", ADMIN_ROUTES)
def test_ca_rp_13_admin_route_cell(make_admin, world, name, who):  # noqa: F811
    account = account_for(make_admin, world, who)
    client = client_for(account)
    url = url_for(name, world)
    for method in ("GET", "POST"):  # GET primer: el POST pot canviar l'objecte
        response = getattr(client, method.lower())(url)
        if who == PERSONAL:
            # El compte personal no entra a l'administració: cap a l'entrada d'administració.
            assert is_login_redirect(response, "administration:login"), (method, response)
            continue
        allowed = all(has_perm(account, code, write=w) for code, w in ROUTES[name][method])
        if allowed:
            assert response.status_code != 404, method
            assert not is_login_redirect(response, "administration:login"), method
        else:
            assert response.status_code == 404, method


# Objecte de cada acció declarada a `ACTIONS`.
OBJECT_FOR_ACTION = {"cancel_supplement": "change"}


@pytest.mark.parametrize("who", ROLES)
@pytest.mark.parametrize("route_action", sorted(ACTIONS))
def test_ca_rp_13_post_action_cell(make_admin, world, route_action, who):  # noqa: F811
    """Accions de `ACTIONS` × rol (CA-M01-83 per al suplement vençut): el GET de la ruta i
    qualsevol dels permisos de l'acció; sense, «no trobat» i res no canvia."""
    name, action = route_action
    account = make_admin(who)
    target = getattr(world, OBJECT_FOR_ACTION[action])
    url = reverse(name, kwargs={"pk": target.pk})
    before = snapshot()
    response = client_for(account).post(url, {"action": action, "reason": REASON})
    allowed = all(has_perm(account, c, write=w) for c, w in ROUTES[name]["GET"]) and any(
        has_perm(account, c, write=w) for c, w in ACTIONS[route_action]
    )
    if allowed:
        assert response.status_code == 302
    else:
        assert response.status_code == 404
        assert snapshot() == before


@pytest.mark.parametrize("who", ACCOUNTS)
@pytest.mark.parametrize("name", OWN_ROUTES)
def test_ca_rp_13_personal_route_cell(make_admin, world, name, who):  # noqa: F811
    """Àrea del soci: només el compte personal; una sessió d'administració va a l'entrada de
    socis. Una ruta només POST respon 405 al GET, després de la sessió."""
    response = client_for(account_for(make_admin, world, who)).get(url_for(name, world))
    if who == PERSONAL:
        assert response.status_code in (200, 405)
    else:
        assert is_login_redirect(response, "accounts:login")


@pytest.mark.parametrize("who", ROLES)
def test_admin_home_links_match_the_route_permissions(make_admin, world, who):  # noqa: F811
    """Cap enllaç del 01 a l'inici de l'administració surt sense el permís de la ruta (només
    ajuda: el control és el de la vista)."""
    account = make_admin(who)
    page = client_for(account).get(reverse("administration:home")).content.decode()
    for name in ADMIN_ROUTES:
        if MODULE_ROUTES[name]:
            continue  # rutes d'un objecte: no surten a l'inici
        link = f'href="{reverse(name)}"'
        if link in page:
            assert all(has_perm(account, c, write=w) for c, w in ROUTES[name]["GET"]), name


# --- Abast d'objecte: el soci només veu el seu ------------------------------------------------


@pytest.mark.parametrize("name", [n for n in OWN_ROUTES if MODULE_ROUTES[n]])
def test_object_of_another_person_is_not_found_and_recorded(make_admin, world, name):  # noqa: F811
    """Amb l'identificador d'un objecte d'un altre soci: «no trobat» i l'intent al registre
    (CA-M01-25, RN-M01-77). Les altres rutes de l'àrea no porten cap identificador."""
    (param,) = MODULE_ROUTES[name]
    target = {"record_id": world.record, "fee_id": world.fee}[param]
    url = reverse(name, kwargs={param: target.pk})
    client = client_for(world.personal)
    response = client.get(url)
    if response.status_code == 405:
        response = client.post(url, {})
    assert response.status_code == 404
    attempt = AuditEntry.objects.get(action=audit.Action.PERSONAL_AREA_NOT_FOUND)
    assert attempt.actor_account == world.personal
    assert attempt.target_id == str(target.pk)


def test_admin_account_cannot_declare_its_own_expiry(make_admin, world):  # noqa: F811
    """Una acció pròpia es fa amb el compte personal: el compte d'administrador de la mateixa
    persona rep «no trobat» del servei (059, punt 4.2)."""
    admin = make_admin("secretary", person=world.own.person)
    with pytest.raises(Http404):
        licences.declare_expiry(world.own_record, by=admin, expires_on=datetime.date(2026, 12, 31))
    world.own_record.refresh_from_db()
    assert world.own_record.expires_on is None


# --- Serveis: el permís també fora de la vista ------------------------------------------------

TODAY = local_today()
LICENCE = {
    "licence_type": "Anual FECDAS",
    "issued_on": datetime.date(2026, 1, 15),
    "expires_on": datetime.date(2026, 12, 31),
}
P = "members."


def _due_today(fee):
    """Una quota amb el període encara obert, sigui quin sigui el dia que s'executa la prova."""
    fee.due_on = TODAY
    fee.save()
    return fee


SERVICES = {
    # nom: (permisos que calen, crida)
    "approve_join": (
        ((P + "requests.approve_join", True),),
        lambda w, by: admissions.approve_join(w.join_request, by=by),
    ),
    "reject_join": (
        ((P + "requests.approve_join", True),),
        lambda w, by: admissions.reject_join(w.join_request, by=by, reason=REASON),
    ),
    "approve_leave": (
        ((P + "requests.resolve_change", True),),
        lambda w, by: member_requests.approve_leave(w.leave, by=by, effective_on=TODAY),
    ),
    "reject_request": (
        ((P + "requests.resolve_change", True),),
        lambda w, by: member_requests.reject(w.leave, by=by, reason=REASON),
    ),
    "create_leave": (
        ((P + "requests.resolve_change", True),),
        lambda w, by: member_requests.request_leave(w.other, by=by, reason=REASON),
    ),
    "cancel_supplement": (
        # 075 (RN-M01-82): P7a o P8, tots dos amb edició (una llista és «qualsevol d'aquests»).
        ([(P + "requests.cancel_supplement", True), (P + "fees.generate", True)],),
        lambda w, by: member_requests.cancel_overdue_supplement(w.change, by=by, reason=REASON),
    ),
    "cancel_fee": (
        # 072 (quarta instrucció, punt 4) i 085: el mateix permís que l'exempció (P22).
        ((P + "fees.exempt", True),),
        lambda w, by: fees.cancel_fee(w.fee, by=by, reason=REASON),
    ),
    "exempt_fee": (
        ((P + "fees.exempt", True),),
        lambda w, by: fees.exempt_fee(_due_today(w.fee), by=by, reason=REASON),
    ),
    "mark_unpaid": (
        ((P + "unpaid.mark", True),),
        lambda w, by: services.mark_unpaid(w.other, by=by, effective_on=TODAY, reason=REASON),
    ),
    "unmark_unpaid": (
        ((P + "unpaid.mark", True),),
        lambda w, by: services.unmark_unpaid(w.other, by=by, effective_on=TODAY, reason=REASON),
    ),
    "add_licence": (
        ((P + "licence_record.manage", True), (P + "list", False)),
        lambda w, by: licences.add_record(w.other, by=by, **LICENCE),
    ),
    "correct_licence": (
        ((P + "licence_record.manage", True), (P + "list", False)),
        lambda w, by: licences.correct_record(w.record, by=by, **LICENCE),
    ),
    "confirm_in_bulk": (
        ((P + "licence_record.manage", True), (P + "list", False)),
        lambda w, by: licences.confirm_in_bulk([w.record.pk], year=2026, by=by),
    ),
    "edit_member": (
        ((P + "edit", True), (P + "list", False)),
        lambda w, by: member_edit.edit_member_data(w.other, by=by, fields={"first_name": "Nou"}),
    ),
    "correct_join_date": (
        ((P + "edit_join_date", True), (P + "list", True)),
        lambda w, by: member_edit.correct_join_date(
            w.other,
            by=by,
            joined_on=datetime.date(2010, 1, 1),
            approximate=False,
            reason=REASON,
        ),
    ),
    # 079 (RN-M01-87): tornar a enviar la invitació del compte personal, amb M2 i P4.
    "resend_invitation": (
        (("core.people.manage", True), (P + "list", False)),
        lambda w, by: admissions.resend_invitation(w.other, by=by),
    ),
    # 079 (A-21, RN-M01-92): revocar el carnet d'un soci, amb P21 i P4.
    "revoke_card": (
        ((P + "card.revoke", True), (P + "list", False)),
        lambda w, by: cards.revoke_by_admin(w.other, by=by, reason=REASON),
    ),
    "join_in_person": (
        ((P + "create_in_person", True),),
        lambda w, by: join.submit({}, channel=MemberRequest.Channel.IN_PERSON, by=by),
    ),
}


def allows(account, need) -> bool:
    """`(codi, edició)`, o una llista d'alternatives de les quals n'hi ha prou amb una."""
    alternatives = need if isinstance(need, list) else [need]
    return any(has_perm(account, code, write=w) for code, w in alternatives)


def snapshot():
    return (
        list(MemberRequest.objects.order_by("pk").values_list("pk", "status")),
        list(Member.objects.order_by("pk").values_list("pk", "status", "joined_on")),
        list(LicenceRecord.objects.order_by("pk").values_list("pk", "licence_type", "expires_on")),
        list(Charge.objects.order_by("pk").values_list("pk", "status")),
        list(Person.objects.order_by("pk").values_list("pk", "first_name")),
        AuditEntry.objects.count(),
    )


@pytest.mark.parametrize("who", ACCOUNTS)
@pytest.mark.parametrize("service", sorted(SERVICES))
def test_service_checks_the_permission_outside_the_view(make_admin, world, service, who):  # noqa: F811
    needs, call = SERVICES[service]
    by = account_for(make_admin, world, who)
    allowed = all(allows(by, need) for need in needs)
    if not allowed:
        before = snapshot()
        with pytest.raises(Http404):
            call(world, by)
        assert snapshot() == before
        return
    try:
        call(world, by)
    except (ValidationError, KeyError):  # una regla de negoci o la dada buida, ja passat el permís
        pass
