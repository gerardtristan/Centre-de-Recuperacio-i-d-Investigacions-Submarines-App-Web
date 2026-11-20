# Fase 1: dades per a l'informe de tancament (20/11/2026)

Dades per a l'informe de tancament de la fase 1. Contrastades amb `master` a `9e1d9b2` i revisades a la volta final (`2f48be1c`, apartat 6). **No dona cap porta per superada.** Cada nivell demana, a més, l'autorització expressa i per escrit de la junta ([025](../decisions/025-dos-nivells-de-produccio.md)). Segons la [092](../decisions/092-carril-extern-amb-proveidor-i-banc-ficticis.md), punt 7, cap nivell no s'encén sense el proveïdor i el banc reals.

Estats: **fet** (hi ha evidència al codi o a les proves), **parcial**, **no fet** (ho pot fer l'equip) i **extern** (depèn del servidor, del proveïdor, del banc, de la junta, de la gestoria o del propietari).

## 1. Nivell 1: producció de mandats

### Portes 0 a 2 ([checklist](../checklist-produccio.md#3-llista-per-categories))

| Punt | Estat | Evidència o què falta | Qui |
|---|---|---|---|
| A1 CI | parcial | `ci.yml`: proves amb cobertura ≥ 97,6 %, lint, migracions, `check --deploy`, e2e i gitleaks. Falta el desplegament a staging i a producció | Propietari (servidor) |
| A2 Ambients | parcial | `config/settings/` té `dev`, `test`, `staging` i `prod`. L'staging és el servidor de proves del portàtil ([099](../decisions/099-servidor-de-proves-al-portatil.md), #251). No hi ha producció | Propietari |
| A3 Secrets | fet | gitleaks al CI; secrets només a l'entorn (`.gitleaks.toml`) | — |
| A4 Rotar claus filtrades | parcial | Hi ha rotació per a les claus del QR (`reemet_carnets`), de l'IBAN (`rota_clau_mandats`) i de `FIELD_ENCRYPTION_KEYS` ([arquitectura](../arquitectura-integracions.md) §8). Falten el procediment general i el simulacre | Equip; simulacre al servidor |
| A5 README | fet | `README.md` | — |
| A7 Domini i SSL | extern | Sense servidor | Propietari ([O3](fase1-pendents-externs.md#propietari)) |
| B1 Proves unitàries | parcial | Llindar de cobertura del 97,6 % al CI. No es mesura a part que els càlculs econòmics tinguin el 100 % | Equip |
| B2 Proves de fum | parcial | `test_smoke.py` (e2e) al CI. Encara no es passa després de cada desplegament (no n'hi ha cap) | Propietari (servidor) |
| B3, B7, B9 | fet | Prova abans de cada arreglo; 404 i 500 pròpies (T-M01-47); importacions de Cluber i de l'extracte amb casos incorrectes | — |
| B4 Permisos | fet | Proves per cel·la de la matriu i rutes (`test_route_permissions.py`, `test_access.py`) | — |
| C1 Autenticació a cada endpoint | fet | `apps/core/tests/test_access.py` (`PUBLIC_ROUTES` declarades) | — |
| C2, C4, C5 Comptes, doble factor, restabliment, verificació | fet | T-M01-05, T-M00-03 i T-M01-51 | — |
| C3 Limitació de peticions | fet | `apps/accounts/limits.py` i els límits del formulari «Fer-se soci» | — |
| C6 Auditoria de dependències | fet (#304) | Pas «Auditoria de dependències» (`pip-audit`) al job `proves` del CI. La primera auditoria va trobar la PYSEC-2026-1845 a pytest 8.4.2, que es resol amb pytest ≥ 9.0.3. Queda la revisió mensual | Equip |
| C7 Configuració de producció | fet | `check --deploy --fail-level WARNING` al CI i a `tools/verifica.py` (#286) | — |
| C8 Registre d'activitat | fet | `core.AuditEntry`, només s'hi afegeixen files (disparadors) | — |
| C9 Pagaments | fet (amb proveïdor fals) | Firma i idempotència del webhook; `PAYMENTS_LIVE_CHARGES_ALLOWED` apagat al nivell 1. Falta el proveïdor real | PaynoPain ([PP](fase1-pendents-externs.md#paynopain)) |
| C10 Fitxers pujats | fet | Fitxers privats amb tipus i mida limitats (`core.PrivateFile`) | — |
| C11 Dos usuaris de base de dades | extern | [P-80](M00.md) «per fer», es fa en desplegar | Propietari (servidor) |
| C12, C13 Claus del QR i de l'IBAN | parcial | Codi, comprovacions d'arrencada i rotació fets (`test_crypto.py`). Falta la prova de restauració d'una còpia real amb la clau (044) | Propietari (servidor) |
| D1, D2, D3 Còpies, restauració, límits de despesa | extern | Disseny a l'[arquitectura](../arquitectura-integracions.md) (bolcat diari xifrat a Scaleway i Storage Box). Res configurat | Propietari (servidor) |
| D4 Allotjament a la UE | fet (documentat) | [Arquitectura](../arquitectura-integracions.md) | — |
| D5 Migracions amb dades de staging | extern | Sense staging permanent | Propietari |
| E1 Registres | parcial | `LOGGING` a la consola, sense dades personals per disseny. Falta revisar exemples reals | Equip, al servidor |
| E2 Seguiment d'errors | parcial | Codi fet (E4, #183 i #192). Encendre'l és la [E4b](M00.md), que espera el servidor | Propietari |
| G1 SPF, DKIM, DMARC (cris.es) | extern | Cal accés al DNS de cris.es | Propietari o junta |
| G2 Butlletins i baixa | no aplica encara | La plataforma no envia butlletins a la fase 1; el consentiment «newsletter» es pot retirar des del perfil | — |
| H1 Privacitat i condicions | extern | Textos de l'equip publicats i provisionals; falten la revisió i l'aprovació ([T-M01-16b](M01.md)) | Gestoria ([G3, G4](fase1-pendents-externs.md#gestoria)) i junta ([J2](fase1-pendents-externs.md#junta)) |
| H3 Esborrat i exportació | fet | T-M01-22 i T-M00-04. Queden obertes la [P-416](../decisions/pendents.md) (interruptor apagat), la [P-418](../decisions/pendents.md) i la [P-420](../decisions/pendents.md) | — |
| H4 Sense dades de salut | fet | Cap camp de salut al model | — |

### Punts «N1» de la porta 3

| Punt | Estat | Evidència o què falta | Qui |
|---|---|---|---|
| A6 Marxa enrere | extern | [T-M05a-19](../planning.md#M05a-10-tasques) sense fila d'estat: «reversió provada a staging». La [guia de mandats](../guies/guia-mandats.md) ho dona per pendent | Propietari (servidor) |
| E3 Monitoratge de la web i del flux | parcial | `/salut/` públic i sense estat intern (`apps/core/views/__init__.py::health`). El monitor extern no està configurat | Propietari (servidor) |
| E4 Alertes (caiguda, errors, certificat, còpia fallida) | extern | Seguiment d'errors al codi; la resta, al servidor (T-M05a-19, E4b) | Propietari |
| B5 Flux de mandat en mòbil | parcial | [Mesura del 17/11](../mesures/T-M05a-18-accessibilitat-mandat.md): Chromium a 1280, 390 i 320 px, en clar i en fosc. Falten un iPhone i un Android reals ([T-M05a-18b](M05a.md)) | Propietari ([O2](fase1-pendents-externs.md#propietari)) |
| B8 Accessibilitat bàsica del flux | fet, amb una incidència | Mateixa mesura: axe sense violacions greus i teclat correcte. Incidència: contrast de la barra inferior en fosc ([P-283](../decisions/pendents.md), `xfail`). Falta el lector de pantalla real | Propietari (lector) i DISSENY (P-283) |
| G3 Correu de confirmació del mandat | fet (amb proveïdor fals) | Plantilla `mandat-signat` (`test_mandate_signing.py`). El text és provisional [A validar: junta] | Junta (text) |

## 2. Nivell 2: producció completa

Punt per punt a [portes-nivell-2.md](portes-nivell-2.md) (T-M05b-19, 17/11/2026). Contrastat avui amb `master`:

| Punt | Estat avui | Canvi des del 17/11 |
|---|---|---|
| B5 (N2) | parcial | El CI ja instal·la Firefox i WebKit (`ci.yml`), però només les fa servir `test_logotip.py`; ni tauleta ni telèfons reals |
| B6 Xarxa lenta | parcial | Cap |
| B8 (N2) WCAG 2.2 AA | parcial | Cap; falten el lector de pantalla i la revisió manual ([T-M01-28b](M01.md), bloquejada) |
| E3 (N2) i E4 (despesa) | extern | Cap: servidor |
| E5 Rendiment | no fet | Cap |
| E6 Analítica | parcial | Cap |
| F1, F2, F3 (web pública) | no fet | Cap: són de la 07, a la fase 2 ([P-300](../decisions/pendents.md)) |
| F4 Favicon i OG | parcial | Cap: sense `rel="icon"` ni `og:` |
| F5 Imatges | fet | — |
| F6 Memòria cau | parcial | Cap: `StaticFilesStorage` sense empremta |
| F7 Idioma | parcial | Cap ([P-49](../decisions/pendents.md)) |
| H2 Cookies | parcial | Cap |
| H5 Menors | extern | Junta ([P-33](../decisions/pendents.md)) |

A més: el proveïdor i el banc reals ([T-M05b-19b](M05b.md)), i les P irreversibles de l'apartat 4 que bloquegen el nivell 2.

## 3. Externs

Llista completa, amb les preguntes a punt per enviar: [fase1-pendents-externs.md](fase1-pendents-externs.md) (#254).

| Responsable | Preguntes |
|---|---|
| Banc (a través del tresorer) | 8 |
| PaynoPain | 8 |
| Junta | 6 |
| Tresorer | 3 |
| Gestoria o assessor de protecció de dades | 5 |
| Propietari | 6 |
| **Total** | **36** |

## 4. Pendents irreversibles oberts que bloquegen un nivell

Font: [pendents.md](../decisions/pendents.md), secció Oberts. La P-406 i la P-408 ja estan resoltes (#287).

| P | Tema | Bloqueja | Respon |
|---|---|---|---|
| P-44, P-45 | Banc, TPV i preguntes al proveïdor | Els dos nivells (092 §7) | Banc, PaynoPain |
| P-21 | Mandats actuals (escenari B, campanya) | El nivell 1, si Cluber cedeix els mandats | Junta, banc |
| P-24 | Identificador de creditor | El nivell 1 (avisos previs i rebuts) | Banc |
| P-123 | Països de l'IBAN admesos al mandat | Encendre la signatura a producció (nivell 1) | Banc, via el tresorer |
| P-233, P-237, P-291 | pain.008, abonament de la remesa, codis de retorn | El nivell 2 | Banc i tresorer |
| P-416 | Exportació RGPD amb les notes de l'administració | Encendre l'interruptor (no bloqueja cap nivell; apagat) | Propietari, amb l'assessor |
| P-418 | Dret d'accés d'un menor de 14 anys | L'accés d'un menor per la plataforma | Propietari, amb l'assessor |
| P-420 | Referències dels pagaments d'una persona esborrada | Abans del nivell 2, la revisió RGPD (H1) | Propietari, amb l'assessor |
| P-02, P-47 | Facturació i IVA | Cap nivell de la fase 1 (és la 09) | Gestoria |

Les altres irreversibles obertes (P-116, P-286, P-298, P-377, P-386, P-401 i P-412) diuen «Bloqueja: res».

## 5. Decisions del propietari abans del nivell 1

| Decisió | Per què | On |
|---|---|---|
| Treure les etiquetes internes visibles per al soci (V17) | Les pantalles del mandat, de la revocació i de la targeta guardada mostren «A validar: junta i banc (L-M05a-01)», «A verificar: P-45 punt 6» i similars, i un soci real les veuria. Cal decidir si s'amaguen a producció o si es treuen quan la junta aprovi els textos | [Informe T-F1-01](T-F1-01-informe.md#71-pendents-visuals-del-04-el-05a-el-05b-i-la-prova-de-cluber) |
| El sí a la llista visual per a DISSENY | V3, V4, V5/V19, V8, V10, V13, V14, V15, V18, V20 i V11, ja passades a la sessió de disseny; cal el sí per fer-les abans del nivell 1 o deixar-les per després | [Informe T-F1-01](T-F1-01-informe.md#73-llista-per-a-la-sessió-de-disseny), 7.3 |
| L'entorn de proves per a mòbils reals | B5 i B8 «N1» (T-M05a-18b), T-M01-21b, T-M01-28b i T-F1-02 esperen un entorn al qual accedeixi un mòbil. El servidor del portàtil (#251, [099](../decisions/099-servidor-de-proves-al-portatil.md)) s'ha d'alleugerir perquè funcioni amb 4 GB de RAM | [O2](fase1-pendents-externs.md#propietari) |
| El servidor de producció | A7, C11, D1 a D3, E2 a E4, A6: tot el que és «extern (servidor)» a l'apartat 1 | [O3](fase1-pendents-externs.md#propietari) |

## 6. Volta final (20/11/2026, `master` a `2f48be1c`)

| Comprovació | Resultat |
|---|---|
| `tools/verifica.py` | **VERD** (empremta `c83b03279940`): 8148 proves, ruff, migracions, `check`, `check --deploy` i 186 e2e |
| `pip-audit --skip-editable` | Net. Al venv del portàtil va avisar del `pip` 25.0.1 (PYSEC-2026-1795 i altres; el CI fa servir el seu `pip`), i s'ha actualitzat a la 26.3 |
| Valors de negoci al codi (#287, #297, #300, #303, #305) | Cap de nou. Els nous són ajustos (VC-16, mesos de l'avís de renovació), regles de seguretat (cua de recuperació, 5 minuts, Q-085) o llistes tancades (orígens del pagament) |
| C6 | Feta (#304) |
| T-M05a-19 | Té fila a [M05a](M05a.md): bloquejada, espera el servidor |

Res d'això no canvia els apartats 1 a 5: els nivells 1 i 2 continuen esperant el servidor de producció, el proveïdor i el banc reals, i l'autorització de la junta.

