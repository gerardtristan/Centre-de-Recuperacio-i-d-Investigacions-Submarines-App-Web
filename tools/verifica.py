"""Verificació completa (T-M00-07, CA-M00-07f; decisió 081, punt 1): segona de les tres capes de
`tools/verificacio.py`.

    python tools/verifica.py

Passa el mateix que el CI: totes les proves (`pytest`, també axe), ruff, `ruff format --check`,
`makemigrations --check`, `manage.py check`, la comprovació de desplegament amb la configuració
de producció i valors de mostra generats en cada execució (cap secret real), i la suite e2e
sencera. És **obligatòria abans del commit quan el hook l'ha deixada pendent**.

- El resultat es desa per a l'empremta exacta del contingut verificat. Si el contingut canvia
  durant l'execució, el resultat no es desa com a verd.
- Una sola execució alhora (el hook i aquesta fan servir la mateixa base de proves): si n'hi ha
  una altra en marxa, aquesta no comença i ho diu. No atura mai el procés d'un altre.
- Sense límit de temps, però en primer pla: si s'interromp (Ctrl+C), mata el seu arbre de
  processos i no deixa res en segon pla.
- Codi de sortida: 0 verd, 1 vermell, 3 una altra verificació en marxa.
"""

import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import verificacio  # noqa: E402

ROOT = verificacio.ROOT


def deploy_env() -> dict:
    """Com el pas «Comprovació de desplegament» del CI: valors de mostra, mai secrets reals."""
    from cryptography.fernet import Fernet

    env = dict(os.environ)
    env.update(
        {
            "DJANGO_SETTINGS_MODULE": "config.settings.prod",
            "DJANGO_SECRET_KEY": secrets.token_urlsafe(50),
            "FIELD_ENCRYPTION_KEYS": Fernet.generate_key().decode(),
            "CARD_QR_KEYS": f"ci:{secrets.token_urlsafe(32)}",
            "CARD_QR_ACTIVE_KEY": "ci",
            "DJANGO_ALLOWED_HOSTS": "cris1954.cat",
            "EMAIL_HOST": "smtp.example.invalid",
            "EMAIL_HOST_USER": "proves",
            "EMAIL_HOST_PASSWORD": "contrasenya-de-proves-1954",
            "S3_BUCKET_FITXERS": "cris-ci",
            "S3_ENDPOINT_URL": "https://s3.example.invalid",
            "S3_ACCESS_KEY_ID": "proves",
            "S3_SECRET_ACCESS_KEY": "contrasenya-de-proves-1954",
        }
    )
    env.setdefault("DATABASE_URL", "postgres://cris:cris-ci@localhost:5432/cris")
    return env


def steps(py: str) -> list[tuple[str, list[str], dict | None]]:
    junit = str(ROOT / verificacio.STATE_DIR_NAME / ".verifica-junit.xml")
    return [
        ("pytest", [py, "-m", "pytest", "-q", "-p", "no:cacheprovider"], None),
        ("ruff", [py, "-m", "ruff", "check", "."], None),
        ("ruff format", [py, "-m", "ruff", "format", "--check", "."], None),
        ("migracions", [py, "manage.py", "makemigrations", "--check", "--dry-run"], None),
        ("check", [py, "manage.py", "check"], None),
        (
            "check --deploy",
            [py, "manage.py", "check", "--deploy", "--fail-level", "WARNING"],
            deploy_env(),
        ),
        (
            "e2e",
            [
                py,
                "-m",
                "pytest",
                "-m",
                "e2e",
                "apps/core/tests/e2e",
                "-q",
                "-p",
                "no:cacheprovider",
                "--create-db",
                f"--junitxml={junit}",
            ],
            None,
        ),  # fmt: skip
    ]


def main() -> int:
    snap = verificacio.snapshot(ROOT)
    fp = verificacio.fingerprint(snap)
    try:
        lock = verificacio.Lock("verificació completa", fp, ROOT).acquire()
    except verificacio.Busy as busy:
        print(
            f"Ja hi ha una verificació en marxa (procés {busy.holder.get('pid')}, "
            f"{busy.holder.get('what')}). No se'n comença cap altra."
        )
        return 3
    results = {}
    try:
        py = verificacio.python(ROOT)
        for name, command, env in steps(py):
            print(f"== {name}", flush=True)
            result = verificacio.run(command, cwd=ROOT, env=env)
            print("\n".join(result.output.strip().splitlines()[-4:]), flush=True)
            results[name] = {"ok": result.ok, "seconds": round(result.seconds, 1)}
        junit = ROOT / verificacio.STATE_DIR_NAME / ".verifica-junit.xml"
        ok = all(step["ok"] for step in results.values())
        state = verificacio.load_state(ROOT)
        state["durations"].update(verificacio.durations_from_junit(junit))
        changed = verificacio.fingerprint(verificacio.snapshot(ROOT)) != fp
        if changed:
            print(
                "El contingut ha canviat durant la verificació: el resultat no es desa com a verd."
            )
        verificacio.record_full(state, fp, snap, ok and not changed, results)
        verificacio.save_state(state, ROOT)
    finally:
        lock.release()
    verdict = "VERD" if ok and not changed else "VERMELL"
    failed = [name for name, step in results.items() if not step["ok"]]
    print(f"{verdict} {fp[:12]}" + (f" (falla: {', '.join(failed)})" if failed else ""))
    return 0 if verdict == "VERD" else 1


if __name__ == "__main__":
    sys.exit(main())
