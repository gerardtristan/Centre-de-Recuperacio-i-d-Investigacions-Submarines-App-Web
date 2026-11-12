"""Exportació de Cluber inventada (071, punt 19): 40 socis en Windows-1252 amb la capçalera real.

La fan servir les proves de la importació i l'ordre `seed_demo_data` (T-M01-27). Només dades
inventades: noms «Inventat», correus `@example.org` i IBAN clarament falsos, sense cap format
vàlid (l'ordre de dades de prova els deixa buits).
"""

import csv
import io

from . import cluber

FALSE_IBAN = "ES00IBANFALS"  # prefix de tots els IBAN inventats de la mostra
LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"

SAMPLE_QUOTAS = (
    ("Quota de soci col·laborador 35€.", "35"),  # pel preu (o pendent si dos tipus el comparteixen)
    ("Quota de soci Ple Dret 90 €.", "90,00"),  # pel nom
    ("QUOTA SIMPATITZANT 35€", "35"),  # pel nom, amb majúscules
    ("Quota familiar 50€.", "50"),  # cap tipus amb aquest preu: pendent
    ("Quota juvenil 35€", "35"),  # pel nom si hi ha el tipus «Juvenil»
)
NAMES = ("Àngels", "Jordi", "Núria", "Pere", "Mònica", "Ferran", "Laia", "Iñaki")


def dni(n):
    """Document amb el format d'un DNI i la lletra correcta, inventat."""
    return f"{n:08d}{LETTERS[n % 23]}"


def fake_iban(n):
    return f"{FALSE_IBAN}{n:012d}"


def real_headers():
    """Capçalera de l'exportació real: la de la mostra parcial amb «IBAN» després de «Soci
    titular» (071, punt 19)."""
    headers = list(cluber.KNOWN_HEADERS)
    headers.insert(headers.index("Soci titular") + 1, "IBAN")
    return headers


def sample_records(count=40):
    rows = []
    for n in range(1, count + 1):
        quota, total = SAMPLE_QUOTAS[n % len(SAMPLE_QUOTAS)]
        rows.append(
            {
                "Nº Soci": str(n),
                "Nom": NAMES[n % len(NAMES)],
                "Cognoms": f"Garcia Inventat{n}",
                "Telèfon": f"346000000{n:02d}",
                "Document d'Identitat": dni(5000 + n),
                "Quota": quota,
                "Preu total": total,
                "Estat": "Activo" if n % 2 else "Pendiente",
                "Soci titular": "",
                "IBAN": fake_iban(n),
                "Email": f"soci{n}@example.org",
                "Data alta/renovació": "" if n % 7 == 0 else f"{n % 28 + 1:02d}/10/2026",
                "Mètode de pagament": "Domiciliación",
                "Adreça": f"Carrer de l'Àncora, {n}",
                "Codi Postal": "08001",
                "Ciutat": "-" if n % 3 == 0 else "Barcelona",
                "Província": "Barcelona",
                "Renovació": "Automática",
                "Polítiques de privadesa": "Sí" if n % 5 else "No",
                "Data d'inscripció": "" if n % 6 == 0 else f"{n % 28 + 1}/{n % 12 + 1}/2010",
                "Data de Naixament": "" if n % 4 == 0 else f"{n % 28 + 1:02d}/05/1980",
                "Edat": "46",
                "idInterno": f"cl-{n:05d}",
                cluber.IMAGE_CONSENT: "Sí" if n % 2 else "No",
            }
        )
    return rows


def to_file(rows) -> bytes:
    out = io.StringIO()
    writer = csv.writer(out, delimiter=";", lineterminator="\r\n")
    headers = real_headers()
    writer.writerow(headers)
    for row in rows:
        writer.writerow([row.get(h, "") for h in headers])
    return out.getvalue().encode("cp1252")


def sample_file(count=40):
    return to_file(sample_records(count))
