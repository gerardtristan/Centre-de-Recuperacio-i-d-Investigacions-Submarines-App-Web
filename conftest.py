"""Fixtures comunes de les proves. Només dades inventades."""

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.apps import apps
from django.db import connection, transaction
from django.test import TransactionTestCase

from apps.accounts.models import Account
from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY
from apps.core.models import Person

PASSWORD = "contrasenya-de-proves-1954"  # noqa: S105 (dada inventada de proves)
# Quan una prova necessita una segona o una tercera contrasenya (canviar-la, dues peticions
# alhora). Inventades i identificables pel mateix prefix; no són cap secret (CLAUDE.md).
NEW_PASSWORD = "contrasenya-de-proves-1954-nova"  # noqa: S105 gitleaks:allow (2a contrasenya de proves)
OTHER_PASSWORD = "contrasenya-de-proves-1954-altra"  # noqa: S105 gitleaks:allow (3a contrasenya de proves)


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


class CommittedDataTestCase(TransactionTestCase):
    """Proves de concurrència amb PostgreSQL real: les dades es confirmen de debò perquè els
    fils, cadascun amb la seva connexió, les vegin.

    És un `TransactionTestCase` perquè pytest-django prepari la base de dades de proves, però
    sense el TRUNCATE de la neteja, que els disparadors del registre d'activitat (T-M01-07)
    impedeixen. En acabar, s'esborren les files noves de cada taula dins d'una sola transacció,
    amb els disparadors de l'usuari desactivats només dins d'aquesta transacció (ALTER TABLE és
    transaccional a PostgreSQL). No toca les dades de les migracions (rols, matriu, «General»).

    Dues condicions: (1) tota clau forana s'ha de poder ajornar (DEFERRABLE), perquè l'ordre dels
    DELETE és alfabètic; les que crea Django ja ho són i les compostes amb RunSQL ho han de
    declarar (members/0001). Les de la cua (procrastinate) no, però l'ordre ja els va bé, llevat
    de `procrastinate_periodic_defers`, que cap prova no crea. (2) Només s'esborren les files
    noves: una prova que modifiqui una fila de les migracions (per exemple, el comptador de
    números) l'ha de deixar com estava.
    """

    @classmethod
    def _fixture_setup(cls):
        # Es crida abans de cada prova (Django 5.2 el declara mètode de classe).
        cls._tables, cls._start = committed_snapshot()

    def _fixture_teardown(self):
        delete_committed_rows(self._tables, self._start)


PRIVATE_FILES = "core_privatefile"


def committed_snapshot():
    """Taules amb clau entera i el seu valor màxim abans de la prova (`CommittedDataTestCase` i
    proves e2e, on el servidor en viu té la seva connexió i les dades s'han de confirmar)."""
    # Protecció: mai fora de la base de dades de proves.
    if not connection.settings_dict["NAME"].startswith("test_"):
        raise RuntimeError("Aquestes proves només s'executen a la base de proves.")
    tables = _integer_pk_tables()
    start = {}
    with connection.cursor() as cursor:
        for table, column in tables:
            cursor.execute(f'SELECT COALESCE(MAX("{column}"), 0) FROM "{table}"')  # noqa: S608
            start[table] = cursor.fetchone()[0]
        # Els fitxers privats tenen la clau en UUID: es guarden els que ja hi eren (P-12b, un
        # pagament hi apunta i s'esborren tots dos a la mateixa transacció).
        cursor.execute("SELECT id FROM core_privatefile")
        start[PRIVATE_FILES] = [row[0] for row in cursor.fetchall()]
    return tables, start


def delete_committed_rows(tables, start):
    """Esborra les files noves de cada taula dins d'una sola transacció (vegeu
    `CommittedDataTestCase`)."""
    with transaction.atomic(), connection.cursor() as cursor:
        # Primer es desactiven tots: un ALTER TABLE no es pot fer amb comprovacions de
        # claus foranes pendents a la mateixa taula.
        for table, _ in tables:
            cursor.execute(f'ALTER TABLE "{table}" DISABLE TRIGGER USER')
        # Les restriccions diferibles que es comproven a l'instant (members/0001) esperen
        # al final: l'ordre dels DELETE no segueix el de les claus foranes.
        cursor.execute("SET CONSTRAINTS ALL DEFERRED")
        for table, column in tables:
            cursor.execute(
                f'DELETE FROM "{table}" WHERE "{column}" > %s',  # noqa: S608
                [start[table]],
            )
        cursor.execute(
            "DELETE FROM core_privatefile WHERE NOT (id = ANY(%s))", [start[PRIVATE_FILES]]
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


def run_with_production_settings(code, extra_env=None):
    """Executa `code` amb la configuració de producció en un procés a part, amb valors de mostra
    generats aquí (cap secret real). No envia res ni toca cap base."""
    import os
    import secrets
    import subprocess
    import sys

    from cryptography.fernet import Fernet
    from django.conf import settings

    # Sense les variables de qui executa les proves que canviarien el resultat.
    env = {
        k: v
        for k, v in os.environ.items()
        if k != "EMAIL_ALERT_TO" and not k.startswith("ERROR_TRACKING")
    }
    env.update(
        {
            "DJANGO_SETTINGS_MODULE": "config.settings.prod",
            "DJANGO_SECRET_KEY": secrets.token_urlsafe(50),
            "FIELD_ENCRYPTION_KEYS": Fernet.generate_key().decode(),
            "MANDATE_ENCRYPTION_KEYS": "1:" + Fernet.generate_key().decode(),
            "CARD_QR_KEYS": f"ci:{secrets.token_urlsafe(32)}",
            "CARD_QR_ACTIVE_KEY": "ci",
            "DJANGO_ALLOWED_HOSTS": "cris1954.cat",
            "EMAIL_HOST": "smtp.example.invalid",
            "EMAIL_HOST_USER": "proves",
            "EMAIL_HOST_PASSWORD": PASSWORD,
            "S3_BUCKET_FITXERS": "cris-ci",
            "S3_ENDPOINT_URL": "https://s3.example.invalid",
            "S3_ACCESS_KEY_ID": "proves",
            "S3_SECRET_ACCESS_KEY": PASSWORD,
            **(extra_env or {}),
        }
    )
    env.setdefault("DATABASE_URL", "postgres://cris:cris-ci@localhost:5432/cris")
    return subprocess.run(  # noqa: S603 (ordre fixa de les proves)
        [sys.executable, "-c", code],
        cwd=settings.BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
