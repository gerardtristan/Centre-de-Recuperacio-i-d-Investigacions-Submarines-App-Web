# Revisió: valors i llistes escrits al codi (13/11/2026)

Revisió de només lectura del codi d'aplicació de `master` a `9a46381`, contra la regla de [valors de negoci](../planning.md#regles), l'[apèndix de valors configurables](../planning.md#valors-configurables), la [peça d'ajustos](../planning.md#valors-configurables-055) i la [matriu de permisos](../planning.md#rols-i-permisos-059-matriu) (decisions [055](../decisions/055-ajustos-configurables-i-addendes.md) i [059](../decisions/059-rols-i-permisos-editables.md)). No s'ha canviat cap fitxer de codi. Necessitat del propietari: tot valor i tot element de llista s'ha de poder editar i ampliar des de l'app, amb permisos «veure» i «veure i editar» per rol.

**Abast:** tots els `*.py` d'`apps/` (accounts, core, members, payments, treasury) sense les proves, `templates/` i `config/settings/`. Cerques: constants en majúscules, `timedelta`, `choices`, imports i xifres, «€», dies i hores, noms de departaments. **Límits:** és una lectura estàtica (no s'ha executat res). Tampoc s'han revisat una per una totes les cadenes traduïbles ni `static/js`. Els mòduls 02, 03, 06 i 09 encara no tenen codi a `master`.

## Resum

1. **Cap pantalla d'ajustos existeix encara**, ni cap clau d'ajust carregada: la T-AJ-02 és «per fer» i la T-AJ-01, «en curs» ([M00](M00.md)). Cap mòdul no crida `business_settings.get`.
2. **Cap apartat d'ajustos no té el permís «veure».** El pla només en preveu un, `settings.edit.<clau>` (RN-RP-17, RN-RP-19), i la pantalla la veu qui pot editar algun valor del mòdul (RN-AJ-05). Pregunta nova: [P-75](../decisions/pendents.md) (tauler F-003).
3. **Dos valors al codi sense cap tasca que els faci editables:** el termini del suplement (7 dies) i el text que el repeteix. Un altre valor (els recordatoris de quota) té tasca, però la clau del pla no el pot desar tal com és. Pregunta nova: [P-79](../decisions/pendents.md) (tauler F-007).

## Valors que haurien de ser editables

| Fitxer i línia | Valor | Ajust que el cobriria | Tasca del pla |
|---|---|---|---|
| `apps/members/member_requests.py:85` (es fa servir a la `:373`) | `SUPPLEMENT_DUE_DAYS = 7`: termini per pagar el suplement del canvi a ple dret | Clau nova, per exemple `members.type_change_supplement_due_days` (no és a l'apèndix; RN-M01-76 admet «un sol valor al codi o als ajustos») | **Cal tasca nova** (la T-M01-32 només cobreix VC-01 a VC-04); [P-79](../decisions/pendents.md) |
| `templates/members/personal_change_type.html:26`, `templates/members/request_detail.html:60` | «tindràs una setmana per pagar el suplement», «venç d'aquí a una setmana» | El mateix ajust; el text n'ha de llegir el valor | **Cal tasca nova** (la mateixa); el text en si, [T-M00-08](../planning.md#M01-addenda-085) |
| `config/settings/base.py:126` (es llegeix a `apps/members/fees.py:311`) | `MEMBER_FEE_REMINDER_OFFSETS`, variable d'entorn, per defecte `-15, -1, 0, 15, 30` | VC-02 | [T-M01-32](../planning.md#M01-addenda-055) ([M01](M01.md), per fer). **Atenció:** la clau de VC-02 de l'addenda és «dies abans» (15) i «dies després» (15 i 30), i no pot desar els cinc dies que fa el codi (Q-061, [072](../decisions/072-respostes-del-responsable-a-la-ronda-1-de-pendents.md)). Cal una llista d'enters; [P-79](../decisions/pendents.md) |
| `apps/members/fees.py:91` (camp `annual_fee_cents`, valors inicials a `apps/members/migrations/0002_initial_types_and_counter.py`) | Quota del tipus de soci (3500 i 9000) | VC-01: ja és una dada, però sense pantalla, sense versions i sense data d'entrada en vigor | [T-M01-32](../planning.md#M01-addenda-055) |
| `templates/members/personal_card.html:44` | Text del darrere del carnet («Carnet personal i intransferible…») | VC-03 `members.card_back_text` | [T-M01-32](../planning.md#M01-addenda-055) (el comentari de la plantilla ja ho diu) |
| `templates/emails/` (20 plantilles) i textos de pantalla de `templates/` | Textos dels correus i dels avisos | Model de textos editables (no és un `Setting`) | [T-M00-08](../planning.md#M01-addenda-085) ([M00](M00.md), per fer; falta l'especificació) |
| `apps/core/charges.py:49` i `:59` | Departaments: hi ha els serveis de crear i desactivar, però cap pantalla | VC-08, permís T3 / M7 | Probablement [T-M04-15](../planning.md#M04-10-tasques) («pantalles de tresoreria»), però la fila no esmenta els departaments: **dubte** |

## Dubtes (cal decidir si són valors de negoci)

| Fitxer i línia | Valor | Ajust que el cobriria | Tasca del pla |
|---|---|---|---|
| `config/settings/base.py:166` (es llegeix a `apps/core/locked_data.py:118`) | `LOCKED_DATA_RETENTION_YEARS = 6`, variable d'entorn | Si és editable, `core.locked_data_retention_years`. És un termini legal (085, G-1), i això el decanta cap a «es queda». A part, el docstring d'`apps/core/privacy.py:27-33` és antic: diu que no hi ha cap nombre d'anys, però `locked_data.py` ja aplica els 6 | Cap; **cal tasca nova** si es decideix que és editable |
| `config/settings/base.py:135-137` | Límits del formulari «Fer-se soci» (5 per origen en 60 minuts, 3 per destinatari i dia), variables d'entorn | Són límits contra l'abús (seguretat). Q-040 de la 072 els anomena «valors inicials configurables» | Cap; si són seguretat, no cal |
| `config/settings/base.py:168` | `CLUB_TAX_ID`, variable d'entorn | Dada pública del club; podria anar amb VC-03 o en uns ajustos generals | Cap |
| `apps/members/join.py:49` | `REQUIRED_TEXTS`: quins textos legals són obligatoris | Decisió legal encara oberta (Q-16), no un valor | Cap |
| `apps/members/fee_rules.py:25`, `apps/members/member_requests.py:72` | Codis de tipus `supporter` i `full` dins les regles (RN-M01-64, 073, 074) | Els tipus de soci són dades, però les regles depenen de dos codis fixos: un tipus nou creat des de l'app no tindria cap d'aquestes regles. Tampoc hi ha cap pantalla per crear tipus | Cap |
| `apps/members/tasks.py:10` | `cron="0 6 * * *"`: hora d'enviament de quotes i recordatoris | És un horari, però no és a l'apèndix; probablement tècnic | Cap |

## Considerats i que es queden al codi

Seguretat, integritat, formats o regles aprovades. No són valors de negoci segons la [055](../decisions/055-ajustos-configurables-i-addendes.md), punt 6:

- **Regles d'edat i inici de la quota:** `FULL_TYPE_MIN_AGE = 14` i `FEE_START_OFFSET = 15` (`apps/members/fee_rules.py:22-23`), regles aprovades RN-M01-64 i 65 (068). El +15 és política del club i queda al límit.
- **Seguretat:** `OFFLINE_COPY_DAYS = 30` (`apps/members/cards.py:53`). També la validesa dels enllaços, els bloquejos, els temps de sessió, el mínim de comptes d'emergència i els límits del webhook (`apps/core/guest_links.py`, `apps/accounts/`, `apps/payments/webhooks.py`).
- **Departament «General»:** `Department.GENERAL` (`apps/core/models.py:615`) i les quotes sempre a «General» (`apps/core/charges.py`) són una regla d'integritat (CA-15.8). El departament es troba pel nom i no hi ha cap servei per reanomenar-lo.
- **Llistes tancades:** estats del càrrec, del soci i de la sol·licitud; tipus de compte de tresoreria; mètodes de pagament; codis de rol. Són màquines d'estats o integritat. Quins mètodes s'ofereixen és VC-14 (05a, encara sense codi), i els permisos dels rols ja són dades (059).
- **Renovació:** 12 mesos després del pagament (`apps/members/validity.py:31`), regla 070.
- **Límits tècnics:** límit diari de correus, mida màxima dels fitxers i retenció de les exportacions RGPD (`config/settings/base.py:173-202`).
- **Valors inicials a les migracions de dades:** tipus i quotes, comptes i centres de cost de tresoreria, «General». Només posen el valor inicial; el codi no el repeteix (excepte «General», que és una regla).

## Pantalles d'ajustos i permisos

| Mòdul | Pantalla d'ajustos al codi | Permís «veure» | Permís «veure i editar» |
|---|---|---|---|
| 00 (peça comuna) | No: cap vista, cap ruta, cap plantilla (T-AJ-02, per fer) | No existeix ni és al pla | `settings.edit.<clau>`, comprovat a `apps/core/business_settings.py:157` amb escriptura; sense permís, «no trobat». Cap codi `settings.edit.*` no és encara al catàleg (`apps/core/permission_catalog.py`) |
| 01 | No (T-M01-32, per fer) | No | No (cap clau declarada) |
| 04 | No: els departaments i els comptes no tenen pantalla (VC-08) | La matriu té T1 i T3, però cap «veure» separat per als departaments | T3, M7 (sense pantalla) |
| 05a, 05b | No (T-M05a-22, T-M05b-22) | No | No |

**Conclusió:** cap apartat d'ajustos no compleix encara els dos permisos per rol. El catàleg de permisos ja té l'abast de només lectura (`SCOPE_READ`, «Cons.», `apps/core/permission_catalog.py:25`), i `has_perm(..., write=True)` el rebutja per editar (`apps/core/permissions.py:109`). Es podria fer servir per al «veure» sense un codi de permís nou, però el pla no ho diu. Opcions a [P-75](../decisions/pendents.md).
