"""Fixtures comunes de les proves. Només dades inventades."""

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.apps import apps
from django.db import connection, transaction

from apps.accounts.models import Account
from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY
from apps.core.models import Person

PASSWORD = "contrasenya-de-proves-1954"  # noqa: S105 (dada inventada de proves)


@pytest.fixture
def make_person(db):
    def make(first_name="Anna", last_name="Puig", **fields):
        return Person.objects.create(
            first_name=first_name, last_name=last_name, origin=Person.Origin.WEB, **fields
        )

    return make


@pytest.fixture
def personal_account(make_person):
    account = Account.objects.create_personal(make_person(), "anna@example.org", PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    return account


@pytest.fixture
def admin_account(make_person):
    return Account.objects.create_admin(
        make_person("Joan", "Vila"), "joan.vila", PASSWORD, notification_email="joan@example.org"
    )


def _integer_pk_tables():
    tables = []
    for model in apps.get_models(include_auto_created=True):
        pk = model._meta.pk
        if pk.get_internal_type() in {"AutoField", "BigAutoField", "SmallAutoField"}:
            tables.append((model._meta.db_table, pk.column))
    return sorted(set(tables))


@pytest.fixture
def committed_db(django_db_setup, django_db_blocker):
    """Base de dades sense la transacció de cada prova, per a les proves de concurrència: cada
    fil té la seva connexió i només veu el que s'ha confirmat.

    No es fa servir `transaction=True` de pytest-django perquè la neteja fa TRUNCATE i els
    disparadors del registre d'activitat (T-M01-07) l'impedeixen. En acabar, s'esborren les
    files noves de cada taula dins d'una sola transacció, amb els disparadors de l'usuari
    desactivats només dins d'aquesta transacció (ALTER TABLE és transaccional a PostgreSQL).
    No toca les dades de les migracions (rols, matriu, departament «General»)."""
    with django_db_blocker.unblock():
        tables = _integer_pk_tables()
        start = {}
        with connection.cursor() as cursor:
            for table, column in tables:
                cursor.execute(f'SELECT COALESCE(MAX("{column}"), 0) FROM "{table}"')  # noqa: S608
                start[table] = cursor.fetchone()[0]
        try:
            yield
        finally:
            with transaction.atomic(), connection.cursor() as cursor:
                # Primer es desactiven tots: un ALTER TABLE no es pot fer amb comprovacions
                # de claus foranes pendents a la mateixa taula.
                for table, _ in tables:
                    cursor.execute(f'ALTER TABLE "{table}" DISABLE TRIGGER USER')
                for table, column in tables:
                    cursor.execute(
                        f'DELETE FROM "{table}" WHERE "{column}" > %s',  # noqa: S608
                        [start[table]],
                    )
                cursor.execute("DELETE FROM django_session")
                cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
                for table, _ in tables:
                    cursor.execute(f'ALTER TABLE "{table}" ENABLE TRIGGER USER')


def run_together(functions):
    """Executa les funcions alhora, cadascuna en un fil amb la seva connexió, i en torna els
    resultats en el mateix ordre. Una barrera les fa començar al mateix moment."""
    barrier = threading.Barrier(len(functions))

    def run(function):
        try:
            barrier.wait()
            return function()
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=len(functions)) as pool:
        return list(pool.map(run, functions))


@pytest.fixture
def login_as(client):
    """Obre una sessió com si s'hagués entrat per l'entrada indicada (sense passar pel
    formulari): per a les proves que no són de l'entrada mateixa."""

    def login(account, area):
        client.force_login(account)
        session = client.session
        session[AREA_SESSION_KEY] = area
        session[AUTH_AT_SESSION_KEY] = time.time()
        session.save()
        return client

    return login
