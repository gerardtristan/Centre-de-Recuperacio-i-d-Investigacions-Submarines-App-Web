"""Mesura del temps de resposta de «He oblidat la contrasenya» (T-M01-39, part a).

Eina de desenvolupament. No és cap prova i no entra ni a la suite ni al CI: `pytest` sense
arguments només recull `apps/`. És un mòdul de pytest perquè és pytest qui crea la base de
proves i hi aplica les migracions; així no toca mai la base de desenvolupament.

    pytest tools/mesura_recuperacio.py -s -p no:cacheprovider

Què fa (protocol de «T-M01-39 en detall», part a, al pla):
- Peticions POST al formulari públic amb el client de proves de Django, dins del mateix
  procés: mesura la feina de l'aplicació i de la base de dades, no la xarxa ni el proxy.
- Les dades es confirmen de debò (`CommittedDataTestCase`), perquè el cost de confirmar la
  transacció formi part del temps, i s'esborren en acabar. Només dades inventades.
- Set casos per bloc, en ordre aleatori amb llavor: dues adreces inexistents (la diferència
  entre totes dues dona el soroll), compte personal actiu, actiu limitat per destinatari,
  pendent, desactivat i l'adreça de notificació d'un compte d'administrador.
- Cada petició amb una IP diferent i un compte actiu nou a cada bloc: cap límit no interfereix.
- Blocs d'escalfament descartats i blocs mesurats; per cas: n, mitjana, mediana, p10, p90,
  p95 i p99, i la diferència de medianes respecte a la primera adreça inexistent amb un
  interval de confiança del 95 % (bootstrap aparellat per blocs).
- Sense worker: les tasques d'enviament es queden a la cua, i el programa ho comprova.

Variables d'entorn: `MESURA_BLOCS` (500), `MESURA_ESCALFAMENT` (50) i `MESURA_LLAVOR` (1954).
"""

import datetime
import os
import platform
import random
import re
import statistics
import subprocess
import time

import django
from django.conf import settings
from django.db import connection
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone
from procrastinate.contrib.django.models import ProcrastinateJob

from apps.accounts import limits
from apps.accounts.models import Account, EmailLinkRequest
from apps.core import audit
from apps.core.models import AuditEntry, OutgoingEmail, Person
from conftest import PASSWORD, CommittedDataTestCase

BLOCKS = int(os.environ.get("MESURA_BLOCS", "500"))
WARM_UP = int(os.environ.get("MESURA_ESCALFAMENT", "50"))
SEED = int(os.environ.get("MESURA_LLAVOR", "1954"))
BOOTSTRAP_SAMPLES = 2000

CASES = {
    "inexistent-1": "Adreça inexistent (referència)",
    "inexistent-2": "Adreça inexistent (segona: soroll)",
    "actiu": "Compte personal actiu (correu posat a la cua)",
    "limitat": "Compte actiu limitat per destinatari",
    "pendent": "Compte personal pendent",
    "desactivat": "Compte personal desactivat",
    "administrador": "Adreça de notificació d'un compte d'administrador",
}
REFERENCE = "inexistent-1"
# L'únic que canvia d'una resposta a l'altra: el testimoni CSRF de la plantilla base.
_CSRF_TOKEN = re.compile(rb'"X-CSRFToken": "[^"]*"')
TABLES = (Person, Account, EmailLinkRequest, OutgoingEmail, AuditEntry, ProcrastinateJob)


def _person(n) -> Person:
    return Person.objects.create(
        first_name="Mesura", last_name=f"Inventada {n}", origin=Person.Origin.WEB
    )


def _personal(n, email, status) -> Account:
    account = Account.objects.create_personal(_person(n), email, PASSWORD)
    account.status = status
    account.save()
    return account


def _fixed_addresses() -> dict[str, str]:
    """Els comptes que serveixen per a tots els blocs: cap d'aquests casos no gasta res."""
    limited = _personal("limitat", "mesura-limitat@example.org", Account.Status.ACTIVE)
    # Tres enllaços enviats fa un moment: el límit per destinatari d'una hora ja és ple.
    key = limits.recipient_key(limited.login)
    for n in range(limits.RECIPIENT_WINDOWS[0].max_count):
        EmailLinkRequest.objects.create(
            ip_address=f"192.0.2.{n + 1}",
            purpose=EmailLinkRequest.Purpose.RESET_PASSWORD,
            recipient_hash=key,
        )
    _personal("pendent", "mesura-pendent@example.org", Account.Status.PENDING)
    _personal("desactivat", "mesura-desactivat@example.org", Account.Status.DISABLED)
    Account.objects.create_admin(
        _person("administrador"),
        "mesura.administrador",
        PASSWORD,
        notification_email="mesura-administrador@example.org",
    )
    return {
        "limitat": "mesura-limitat@example.org",
        "pendent": "mesura-pendent@example.org",
        "desactivat": "mesura-desactivat@example.org",
        "administrador": "mesura-administrador@example.org",
    }


def _ip(n: int) -> str:
    return f"10.{n // 65536 % 256}.{n // 256 % 256}.{n % 256}"


def _percentile(values, percent: int) -> float:
    return statistics.quantiles(values, n=100, method="inclusive")[percent - 1]


def _median_differences(times, rng) -> dict[str, tuple[float, float, float]]:
    """Diferència de medianes de cada cas respecte a la referència, amb l'interval del 95 %:
    es tornen a triar blocs sencers, perquè els casos d'un bloc s'han mesurat junts."""
    blocks = len(times[REFERENCE])
    samples = {case: [] for case in CASES if case != REFERENCE}
    for _ in range(BOOTSTRAP_SAMPLES):
        chosen = [rng.randrange(blocks) for _ in range(blocks)]
        reference = statistics.median(times[REFERENCE][i] for i in chosen)
        for case, values in samples.items():
            values.append(statistics.median(times[case][i] for i in chosen) - reference)
    reference = statistics.median(times[REFERENCE])
    result = {}
    for case, values in samples.items():
        # Quaranta parts: la primera frontera és el 2,5 % i l'última, el 97,5 %.
        bounds = statistics.quantiles(values, n=40, method="inclusive")
        result[case] = (statistics.median(times[case]) - reference, bounds[0], bounds[-1])
    return result


def _git(*args) -> str:
    result = subprocess.run(  # noqa: S603 (ordre fixa, sense cap dada de fora)
        ["git", *args],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
        cwd=settings.BASE_DIR,
    )
    return result.stdout.strip()


def _row_counts() -> dict[str, int]:
    return {model._meta.db_table: model.objects.count() for model in TABLES}


def _ms(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


def _report(times, differences, environment, before, after) -> str:
    lines = ["## Entorn", ""]
    lines += [f"- {name}: {value}" for name, value in environment.items()]
    lines += ["", "## Files de les taules implicades", "", "| Taula | Abans | Després |"]
    lines += ["|---|---|---|"]
    lines += [f"| `{table}` | {before[table]} | {after[table]} |" for table in before]
    lines += ["", "## Resultats (mil·lisegons)", ""]
    lines += ["| Cas | n | Mitjana | Mediana | p10 | p90 | p95 | p99 |"]
    lines += ["|---|---|---|---|---|---|---|---|"]
    for case, label in CASES.items():
        values = times[case]
        cells = [statistics.fmean(values), statistics.median(values)]
        cells += [_percentile(values, percent) for percent in (10, 90, 95, 99)]
        lines.append(f"| {label} | {len(values)} | " + " | ".join(map(_ms, cells)) + " |")
    lines += ["", "## Diferència de medianes respecte a la primera adreça inexistent", ""]
    lines += ["| Cas | Diferència (ms) | Interval de confiança del 95 % (ms) |", "|---|---|---|"]
    for case, (difference, low, high) in differences.items():
        lines.append(f"| {CASES[case]} | {_ms(difference)} | de {_ms(low)} a {_ms(high)} |")
    return "\n".join(lines)


@override_settings(NUM_PROXIES=0)
class TestMesuraRecuperacio(CommittedDataTestCase):
    def test_mesura(self):
        rng = random.Random(SEED)  # noqa: S311 (ordre dels casos, no és cap secret)
        url = reverse("accounts:password_reset_request")
        client = Client()
        fixed = _fixed_addresses()
        before = _row_counts()
        started = timezone.localtime()
        times = {case: [] for case in CASES}
        bodies = set()
        request_number = 0

        for block in range(WARM_UP + BLOCKS):
            _personal(block, f"mesura-actiu-{block}@example.org", Account.Status.ACTIVE)
            addresses = {
                **fixed,
                "inexistent-1": f"mesura-ningu-a-{block}@example.org",
                "inexistent-2": f"mesura-ningu-b-{block}@example.org",
                "actiu": f"mesura-actiu-{block}@example.org",
            }
            order = list(CASES)
            rng.shuffle(order)
            for case in order:
                request_number += 1
                data, ip = {"email": addresses[case]}, _ip(request_number)
                start = time.perf_counter_ns()
                response = client.post(url, data, REMOTE_ADDR=ip)
                elapsed = (time.perf_counter_ns() - start) / 1_000_000
                if response.status_code != 200:
                    raise RuntimeError(f"Resposta {response.status_code} al cas «{case}».")
                bodies.add(_CSRF_TOKEN.sub(b"", response.content))
                if block >= WARM_UP:
                    times[case].append(elapsed)

        after = _row_counts()
        self._check_the_cases_did_what_they_say(bodies)
        with connection.cursor() as cursor:
            cursor.execute("SHOW server_version")
            postgres = cursor.fetchone()[0]
        dirty = " (amb canvis sense commit)" if _git("status", "--porcelain") else ""
        seconds = round((timezone.localtime() - started).total_seconds())
        environment = {
            "Data i hora (inici)": started.strftime("%d/%m/%Y %H:%M:%S %Z"),
            "Durada": str(datetime.timedelta(seconds=seconds)),
            "Commit": _git("rev-parse", "--short", "HEAD") + dirty,
            "Python": platform.python_version(),
            "Django": django.get_version(),
            "PostgreSQL": postgres,
            "Sistema": f"{platform.system()} {platform.release()} ({platform.machine()})",
            "Configuració": os.environ.get("DJANGO_SETTINGS_MODULE", ""),
            "Base de dades": connection.settings_dict["NAME"],
            "Worker": "aturat (cap tasca d'enviament s'ha executat durant la mesura)",
            "Blocs": f"{WARM_UP} d'escalfament descartats i {BLOCKS} de mesurats",
            "Llavor": SEED,
        }
        differences = _median_differences(times, rng)
        print("\n" + _report(times, differences, environment, before, after))

    def _check_the_cases_did_what_they_say(self, bodies) -> None:
        """Si un cas no ha fet el que diu el seu nom, la mesura no val."""
        blocks = WARM_UP + BLOCKS
        sent = OutgoingEmail.objects.filter(template="recuperacio-contrasenya")
        limited = AuditEntry.objects.filter(
            action=audit.Action.EMAIL_LINK_LIMITED, details__scope="recipient"
        )
        origin_limited = AuditEntry.objects.filter(
            action=audit.Action.EMAIL_LINK_LIMITED, details__scope="origin"
        )
        todo = ProcrastinateJob.objects.filter(task_name="core.send_email", status="todo")
        checks = {
            "la resposta és idèntica en tots els casos": len(bodies) == 1,
            "un correu per bloc, el del compte actiu": sent.count() == blocks,
            "cap correu ha sortit de la cua (worker aturat)": todo.count() == blocks,
            "una petició limitada per destinatari per bloc": limited.count() == blocks,
            "cap petició limitada per origen": not origin_limited.exists(),
        }
        failed = [name for name, passed in checks.items() if not passed]
        if failed:
            raise RuntimeError("La mesura no val: no es compleix que " + "; ".join(failed) + ".")
