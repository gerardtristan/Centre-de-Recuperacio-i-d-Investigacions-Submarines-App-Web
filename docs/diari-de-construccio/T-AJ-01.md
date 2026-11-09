# T-AJ-01 · Peça comuna d'ajustos

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 09/11/2026 04:30 | b7bfc2e | 1738 | [A comprovar]: sense push |

**En tres línies:** la plataforma ja pot guardar valors de negoci (dies d'avís, imports, textos) com a dades i no al codi. Cada canvi queda amb qui l'ha fet, quan, el valor anterior i, si toca diners, una data d'entrada en vigor, una nota i un correu al tresorer i a la junta. Encara no hi ha cap pantalla ni cap valor carregat: els afegirà cada mòdul.

Estat: **implementada, pendent de validació** del responsable del projecte.

## Què s'ha fet
- Models `Setting` i `SettingVersion` a `core` (migració `core/0012_business_settings`). Les versions només admeten files noves: ho impedeixen l'ORM i uns disparadors de PostgreSQL. Detall: [pla, peça comuna d'ajustos](../planning.md#valors-configurables-055).
- `business_settings.get(key, at)` torna el valor vigent a una data (RN-AJ-01).
- `business_settings.change(...)` comprova al servidor el permís del catàleg `settings.edit.<clau>`; sense permís, o amb una clau que no existeix, respon «no trobat». També comprova el tipus i el rang i, per als valors de diners, la data (avui o més endavant) i la nota. Crea la versió i l'entrada del registre d'activitat dins la mateixa transacció (RN-AJ-02 i 03).
- `business_settings.notify_money_change(...)` envia l'avís per la cua de correu (RN-AJ-04). El fa servir `change` i el poden cridar els catàlegs i les tarifes. Plantilla `avis-canvi-diners`.

## Decisions i perquè
- **Sense `editor_roles`.** El pla (060, RN-RP-17 i RN-RP-19) diu que el permís és del catàleg; la T-RP-05 està retirada. Un ajust sense el seu permís al catàleg és un error de programació (`ImproperlyConfigured`), com qualsevol codi de permís desconegut.
- **Cap clau carregada.** Les claus i les files de la matriu per a `settings.edit.<clau>` són de les pantalles d'ajustos de cada mòdul (T-M01-32, T-M05a-22, T-M05b-22…). Les proves fan servir claus i permisos de prova.
- **Destinataris de l'avís:** comptes d'administrador actius amb el rol Tresorer o Junta, amb correu de notificació, i un correu per adreça. El rol Junta existeix des de la [059](../decisions/059-rols-i-permisos-editables.md). S-AJ-02 (qui rep l'avís com a «junta») continua obert: si la junta vol una llista d'adreces, només cal canviar `money_change_recipients`.
- **TOTP:** el pla no en demana cap per desar un ajust (el TOTP en desar és de l'editor de permisos, RN-RP-06). No s'ha tocat res del TOTP.
- **Supòsits d'implementació** (llistats a la fila del pla): què fa un ajust amb data d'entrada en vigor que no és de diners, el format de «dia i mes», URL només amb `https://`, el valor anterior a la data d'entrada en vigor i el correu amb la clau tècnica.

## Problemes trobats
- Un control de l'entorn (no del projecte) rebutjava les escriptures fetes amb un script en línia. La migració es va editar amb l'editor de fitxers. Cap efecte al codi.

## Com se sap que funciona
- CA-AJ-01: 0 i 91 es rebutgen amb el missatge del rang i sense cap versió; 1 i 90 s'accepten. Hi ha una prova de tipus i de rang per a cadascun dels vuit tipus.
- CA-AJ-02: un rol sense el permís rep «no trobat» i no es crea cap versió. El permís és per clau. Un compte personal, un de desactivat o un a qui s'ha retirat el rol tampoc no hi poden fer res.
- CA-AJ-03: un canvi per demà no és vigent avui i ho és demà. Es rebutgen una data passada, l'absència de data i una nota buida o en blanc. Amb la mateixa data, guanya l'últim canvi, i així es desfà un canvi programat.
- CA-AJ-04: un canvi de diners posa a la cua un sol correu per adreça (tresorer i junta), amb el valor anterior i el nou, qui l'ha canviat, la nota i la data. Un canvi que no és de diners no envia res. Si el correu falla, el canvi es manté i el correu continua a la cua per tornar-ho a provar. També hi ha una prova de la crida des d'un catàleg.
- CA-AJ-05: l'entrada del registre guarda el compte, la persona, els rols, l'hora, el valor anterior, el nou i la nota. Les versions no es poden modificar ni esborrar, ni amb l'ORM ni amb SQL directe.

## Evidències
- Sense captures: la tasca no té pantalla (la pantalla és de la T-AJ-02), i de nit no es pot obrir l'app.
- Sortida de proves · commit b7bfc2e · executada el 09/11/2026 en local (PostgreSQL, base de proves `test_night_taj01`):
  ```
  $ pytest -q -p no:cacheprovider
  1738 passed
  $ ruff check . && ruff format --check .
  All checks passed! / 222 files already formatted
  $ python manage.py makemigrations --check --dry-run
  No changes detected
  ```
- Fragment de codi: `apps/core/business_settings.py · commit b7bfc2e · 09/11/2026`

## Termes nous
- **Ajust** (en anglès: *setting*): valor de negoci que es canvia des de l'app, amb registre i, si toca diners, amb data d'entrada en vigor.
- **Canvi programat**: canvi amb una data d'entrada en vigor futura. Fins a aquella data, continua vigent el valor anterior.
