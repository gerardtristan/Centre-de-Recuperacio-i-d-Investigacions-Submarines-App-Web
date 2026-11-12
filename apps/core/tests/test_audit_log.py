"""Consulta del registre d'activitat (T-M01-07b; HU-14, CA-14.3, checklist C8).

M6 hi veu totes les entrades; P20, només les accions «members.*»; sense permís, «no trobat».
Només dades inventades.
"""

import re
import time
from datetime import datetime, timedelta

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY
from apps.core.models import AuditEntry, Person, Role, RolePermission
from apps.core.tests.conftest import (
    main_of,
    make_admin,  # noqa: F401 (fixture)
)

URL = reverse("administration:audit_log")
TZ = timezone.get_default_timezone()


def at(day, hour=10):
    return datetime(2026, 11, day, hour, 0, tzinfo=TZ)


def client_for(account, area=AREA_ADMIN):
    client = Client()
    client.force_login(account)
    session = client.session
    session[AREA_SESSION_KEY] = area
    session[AUTH_AT_SESSION_KEY] = time.time()
    session.save()
    return client


def entry(action, *, account, when, target=("", ""), field="", old=None, new=None, ip=None):
    """Entrada amb la data fixada (les proves de dates la necessiten). Fora de les proves,
    sempre amb `audit.record`."""
    return AuditEntry.objects.create(
        created_at=when,
        actor_kind="account",
        actor_account=account,
        actor_person_id=account.person_id,
        action=action,
        target_type=target[0],
        target_id=target[1],
        field=field,
        old_value=old,
        new_value=new,
        ip_address=ip,
    )


def actions_in(response):
    return [row["entry"].action for row in response.context["rows"]]


def _person(first, last):
    return Person.objects.create(first_name=first, last_name=last, origin="in_person")


@pytest.fixture
def people(make_admin):  # noqa: F811
    """Comptes i persones diferents: M6 (administrador), P20 (Junta amb P20 i res més, com
    ho deixaria l'editor de permisos) i sense permís (instructor)."""
    board = Role.objects.get(code="board")
    RolePermission.objects.create(role=board, permission_code="members.audit.view", scope="all")
    return {
        "m6": make_admin("administrator", username="marta.m6", person=_person("Marta", "Sala")),
        "p20": make_admin("board", username="pau.p20", person=_person("Pau", "Roca")),
        "none": make_admin("instructor", username="nil.sense", person=_person("Nil", "Mas")),
    }


@pytest.fixture
def log(people):
    m6, p20 = people["m6"], people["p20"]
    return {
        "login": entry(
            "auth.login_succeeded",
            account=m6,
            when=at(1),
            ip="192.0.2.10",
            target=("accounts.account", str(m6.pk)),
        ),
        "status": entry(
            "members.status_changed",
            account=m6,
            when=at(2),
            target=("members.member", "7"),
            field="status",
            old="active",
            new="left",
            ip="192.0.2.11",
        ),
        "type": entry(
            "members.type_changed",
            account=p20,
            when=at(3),
            target=("members.member", "8"),
            field="type",
            old="general",
            new="youth",
        ),
        "address": entry(
            "members.profile_changed",
            account=m6,
            when=at(4),
            target=("members.member", "7"),
            field="address",
            old="Carrer Inventat 1",
            new="Carrer Inventat 2",
        ),
        "role": entry(
            "roles.assigned",
            account=m6,
            when=at(5),
            target=("accounts.account", str(p20.pk)),
            field="role",
            new="board",
        ),
    }


# --- Accés per cel·la (M6, P20, sense permís) -------------------------------------------


def test_m6_sees_every_entry_newest_first(people, log):
    response = client_for(people["m6"]).get(URL)
    assert response.status_code == 200
    assert actions_in(response) == [
        "roles.assigned",
        "members.profile_changed",
        "members.type_changed",
        "members.status_changed",
        "auth.login_succeeded",
    ]


def test_p20_sees_only_member_entries(people, log):
    response = client_for(people["p20"]).get(URL)
    assert response.status_code == 200
    assert actions_in(response) == [
        "members.profile_changed",
        "members.type_changed",
        "members.status_changed",
    ]
    content = response.content.decode()
    assert "auth.login_succeeded" not in content
    assert "roles.assigned" not in content


def test_without_permission_is_not_found(people, log):
    assert client_for(people["none"]).get(URL).status_code == 404


def test_admin_account_without_roles_is_not_found(make_admin, log):  # noqa: F811
    assert client_for(make_admin(username="sense.rols")).get(URL).status_code == 404


def test_personal_session_and_anonymous_never_see_the_log(personal_account, log):
    for client in (client_for(personal_account, AREA_PERSONAL), Client()):
        response = client.get(URL)
        assert response.status_code in {302, 404}
        assert b"members.status_changed" not in response.content


def test_removing_p20_from_the_role_closes_the_screen(people, log):
    RolePermission.objects.filter(role__code="board", permission_code="members.audit.view").delete()
    assert client_for(people["p20"]).get(URL).status_code == 404


def test_admin_home_link_only_with_permission(people):
    home = reverse("administration:home")
    assert URL in client_for(people["m6"]).get(home).content.decode()
    assert URL in client_for(people["p20"]).get(home).content.decode()
    assert URL not in client_for(people["none"]).get(home).content.decode()


# --- P20 també amb filtres i paràmetres manipulats ----------------------------------------


@pytest.mark.parametrize(
    "params",
    [
        {"action": "auth.login_succeeded"},
        {"action": "roles.assigned"},
        {"target_type": "accounts.account"},
        {"account": "marta.m6"},
        {"date_from": "2026-11-01", "date_to": "2026-11-01"},
        {"date_from": "2026-11-05"},
        {"pagina": "999"},
        {"pagina": "-1"},
        {"pagina": "res"},
        {"abast": "all", "permis": "core.audit.view", "show_ip": "1"},
        {"action": "members.x' OR '1'='1"},
    ],
)
def test_p20_never_sees_other_entries_whatever_the_query(people, log, params):
    response = client_for(people["p20"]).get(URL, params)
    assert response.status_code == 200
    assert all(a.startswith("members.") for a in actions_in(response))
    # El text pot repetir el valor manipulat a l'error del filtre; les dades, mai.
    content = response.content.decode()
    assert "192.0.2." not in content
    assert f"accounts.account {people['p20'].pk}" not in content


def test_p20_filter_choices_only_offer_member_values(people, log):
    form = client_for(people["p20"]).get(URL).context["form"]
    actions = [value for value, _ in form.fields["action"].choices if value]
    assert actions == ["members.profile_changed", "members.status_changed", "members.type_changed"]
    assert [v for v, _ in form.fields["target_type"].choices if v] == ["members.member"]


def test_manipulated_choice_is_an_error_and_does_not_filter(people, log):
    response = client_for(people["p20"]).get(URL, {"action": "auth.login_succeeded"})
    assert "action" in response.context["form"].errors
    assert len(actions_in(response)) == 3


# --- Privacitat: IP i camps amb permís de camp --------------------------------------------


def test_ip_only_for_m6(people, log):
    assert "192.0.2.11" in client_for(people["m6"]).get(URL).content.decode()
    p20_page = client_for(people["p20"]).get(URL).content.decode()
    assert "192.0.2.11" not in p20_page
    assert "Adreça IP" not in p20_page


def test_field_permission_values_hidden_without_c2(people, log):
    p20_page = client_for(people["p20"]).get(URL).content.decode()
    assert "Carrer Inventat" not in p20_page
    assert "ocult" in p20_page
    assert "youth" in p20_page  # els camps sense permís de camp es veuen
    m6_page = client_for(people["m6"]).get(URL).content.decode()
    assert "Carrer Inventat 1" in m6_page
    assert "Carrer Inventat 2" in m6_page


# --- Filtres ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"date_from": "2026-11-04"}, ["roles.assigned", "members.profile_changed"]),
        ({"date_to": "2026-11-02"}, ["members.status_changed", "auth.login_succeeded"]),
        ({"date_from": "2026-11-03", "date_to": "2026-11-03"}, ["members.type_changed"]),
        ({"account": "PAU.P20"}, ["members.type_changed"]),
        ({"account": "ningu.existeix"}, []),
        ({"action": "members.status_changed"}, ["members.status_changed"]),
        ({"target_type": "accounts.account"}, ["roles.assigned", "auth.login_succeeded"]),
        (
            {"target_type": "members.member", "target_id": "7"},
            ["members.profile_changed", "members.status_changed"],
        ),
        (
            {
                "date_from": "2026-11-02",
                "date_to": "2026-11-04",
                "account": "marta.m6",
                "action": "members.status_changed",
                "target_type": "members.member",
                "target_id": "7",
            },
            ["members.status_changed"],
        ),
    ],
)
def test_filters(people, log, params, expected):
    response = client_for(people["m6"]).get(URL, params)
    assert response.context["form"].errors == {}
    assert actions_in(response) == expected


def test_date_range_backwards_is_an_error(people, log):
    params = {"date_from": "2026-11-05", "date_to": "2026-11-01"}
    response = client_for(people["m6"]).get(URL, params)
    assert "date_to" in response.context["form"].errors


def test_pagination_keeps_filters_and_order(people):
    for n in range(51):
        entry(
            "members.status_changed",
            account=people["m6"],
            when=at(1, 0) + timedelta(minutes=n),
            target=("members.member", str(n)),
        )
    client = client_for(people["m6"])
    first = client.get(URL, {"action": "members.status_changed"})
    assert len(first.context["rows"]) == 50
    assert first.context["rows"][0]["entry"].target_id == "50"
    content = first.content.decode()
    assert "action=members.status_changed" in content
    assert "pagina=2" in content
    second = client.get(URL, {"action": "members.status_changed", "pagina": "2"})
    assert [r["entry"].target_id for r in second.context["rows"]] == ["0"]


# --- Només lectura (CA-14.3) --------------------------------------------------------------


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
@pytest.mark.parametrize("who", ["m6", "p20"])
def test_no_write_methods(people, log, method, who):
    before = list(AuditEntry.objects.values_list("id", "action", "old_value", "new_value"))
    response = getattr(client_for(people[who]), method)(URL, {"id": log["status"].pk})
    assert response.status_code == 405
    after = list(AuditEntry.objects.values_list("id", "action", "old_value", "new_value"))
    assert after == before


def test_screen_offers_no_way_to_modify_or_delete(people, log):
    content = main_of(client_for(people["m6"]).get(URL).content.decode())
    forms = re.findall(r"<form\b[^>]*>", content)
    assert len(forms) == 1  # només el dels filtres
    assert 'method="get"' in forms[0]
    assert "csrfmiddlewaretoken" not in content
    for marker in (
        "hx-post",
        "hx-put",
        "hx-patch",
        "hx-delete",
        'method="post"',
        "Esborra",
        "Edita",
        "Modifica",
        "Anul·la",
    ):
        assert marker not in content
    # Cap enllaç a una ruta per sota del registre: només el mateix llistat (filtres, pàgines).
    links = re.findall(r'href="([^"]+)"', content)
    assert all(href.split("?")[0] == URL for href in links if href.startswith(URL))


def test_no_route_below_the_log(people, log):
    client = client_for(people["m6"])
    for suffix in (f"{log['status'].pk}/", f"{log['status'].pk}/esborrar/", "esborrar/"):
        assert client.get(URL + suffix).status_code == 404


# --- Q-079 de la 072: canvis de perfil de la persona d'un soci --------------------------------


@pytest.mark.django_db
def test_p20_sees_profile_changes_of_members_only(people):
    from datetime import date

    from apps.members.models import Member, MembershipType

    member_person = _person("Joana", "Soci")
    Member.objects.create(
        person=member_person,
        member_number=501,
        type=MembershipType.objects.get(code="supporter"),
        joined_on=date(2020, 1, 1),
    )
    other_person = _person("Biel", "Nosoci")
    for action, who in (
        ("persons.profile_updated", member_person),
        ("persons.updated", member_person),
        ("persons.profile_updated", other_person),
    ):
        entry(
            action,
            account=people["m6"],
            when=at(5),
            target=("core.person", str(who.pk)),
            field="phone",
            old="600000001",
            new="600000002",
        )
    response = client_for(people["p20"]).get(reverse("administration:audit_log"))
    targets = {r["entry"].target_id for r in response.context["rows"]}
    assert actions_in(response).count("persons.profile_updated") == 1
    assert "persons.updated" in actions_in(response)
    assert str(other_person.pk) not in targets
