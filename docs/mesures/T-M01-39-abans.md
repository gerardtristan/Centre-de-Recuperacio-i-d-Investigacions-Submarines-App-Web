# T-M01-39, part (a): mesura abans del canvi

Temps de resposta de «He oblidat la contrasenya» (`POST /compte/contrasenya/oblidada/`, vista `password_reset_request_view`) segons el cas de l'adreça escrita, **abans** de la part (b) (la cua). Protocol: secció «T-M01-39 en detall (proposta)», part (a), dins de l'[addenda de la 066](../planning.md#M01-addenda-066) del pla. Aquí no es decideix res de la (b) ni de la (c).

## Resum en tres línies
- **La mediana no reprodueix la referència del 03/11/2026** (3,9 ms per a una adreça inexistent i 10,5 ms per a un compte actiu): avui les medianes són de 23 a 29 ms en tots els casos, perquè la màquina estava carregada per altres sessions que executaven proves alhora sobre el mateix PostgreSQL.
- **El percentil 10, que és el menys afectat per la càrrega, sí que mostra la mateixa diferència**: uns 5,8 ms per a una adreça inexistent i de 15 a 16 ms per a un compte actiu (la referència deia 3,9 i 10,5). Un compte actiu limitat, pendent o desactivat queda entremig.
- Segons el criteri del pla («si no la reprodueix, no serveix per avaluar el canvi»), **aquestes dues execucions no serveixen com a «abans» definitiu**. El programa sí: cal tornar-lo a executar amb la màquina sense cap altra càrrega, i amb el worker en marxa, abans de comparar-hi el «després».

## Programa
`tools/mesura_recuperacio.py`. És una eina de desenvolupament, fora de la suite i del CI: `pytest` sense arguments només recull `apps/` (`testpaths` de `pyproject.toml`). És un mòdul de pytest perquè és pytest qui crea la base de proves (`test_<base>`) i hi aplica les migracions: no toca mai la base de desenvolupament ni cap base real, i no cal `runserver`.

    pytest tools/mesura_recuperacio.py -s -p no:cacheprovider --log-level=WARNING

Variables: `MESURA_BLOCS` (500), `MESURA_ESCALFAMENT` (50) i `MESURA_LLAVOR` (1954).

## Mètode
- **Què es mesura.** Un `POST` amb el client de proves de Django, dins del mateix procés: tota la pila de l'aplicació (middleware, formulari, servei `email_links.request_password_reset`, consultes, registre d'activitat, posar el correu a la cua) i la confirmació real de la transacció. No inclou la xarxa, el TLS ni el proxy. Rellotge: `time.perf_counter_ns`.
- **Dades confirmades.** `CommittedDataTestCase`: les dades es confirmen de debò, perquè el cost del `COMMIT` hi compti, i s'esborren en acabar. Només dades inventades (`@example.org`, «Mesura Inventada»).
- **Casos (7 per bloc, en ordre aleatori amb la llavor 1954):** dues adreces inexistents (la diferència entre totes dues és el soroll), compte personal actiu (rep el correu), actiu limitat per destinatari (tres enllaços enviats l'última hora), pendent, desactivat i l'adreça de notificació d'un compte d'administrador.
- **Sense interferències dels límits.** Cada petició porta una IP diferent (`REMOTE_ADDR`, amb `NUM_PROXIES=0`) i cada bloc té un compte actiu nou i dues adreces inexistents noves.
- **Blocs:** 50 d'escalfament descartats i 500 de mesurats (3.850 peticions per execució).
- **Estadística per cas:** n, mitjana, mediana, p10, p90, p95 i p99. Diferència de medianes respecte a la primera adreça inexistent amb un interval de confiança del 95 % per bootstrap (2.000 remostrejos de blocs sencers, perquè els set casos d'un bloc s'han mesurat junts).
- **Comprovacions que invaliden la mesura si fallen:** la resposta és idèntica en tots els casos (llevat del testimoni CSRF de la plantilla base); hi ha exactament un correu per bloc, el del compte actiu; cap correu no ha sortit de la cua; hi ha una petició limitada per destinatari per bloc i cap de limitada per origen. Totes dues execucions les han passades.

## Entorn
| | |
|---|---|
| Data i hora | 11/11/2026, de 02:28 a 02:32 (execució 1) i de 02:33 a 02:37 (execució 2), CET |
| Commit | `b3b3f63` (T-M00-06) més el programa, encara sense commit. El codi mesurat (`apps/accounts/email_links.py`, `limits.py`, la vista i la plantilla) és el mateix que a `c1095a7`; de la T-M00-06, a la petició només hi ha la consulta de la prioritat de la plantilla en un diccionari: el comptador diari actua en enviar, no en posar a la cua |
| Programari | Python 3.12.10, Django 5.2.18, PostgreSQL 16.15, Windows 11 (AMD64) |
| Màquina | Intel Core i5-8400 (6 nuclis, 2,8 GHz), 15,9 GB de RAM, ordinador de sobretaula (sense bateria) |
| Configuració | `config.settings.test` (contrasenyes amb MD5 de proves, correu en memòria) |
| Base de dades | `test_night_a_correu`, nova a cada execució, al PostgreSQL local compartit |
| Worker | aturat: cap tasca d'enviament no s'ha executat durant la mesura |
| Altres processos | **càrrega alta**: altres sessions executaven alhora la suite de proves en altres carpetes, contra el mateix servidor PostgreSQL. Hi havia de 18 a 24 processos de Python en marxa a l'inici i al final de cada execució |

Files de les taules implicades (iguals a les dues execucions):

| Taula | Abans | Després |
|---|---|---|
| `core_person` | 4 | 554 |
| `accounts_account` | 4 | 554 |
| `accounts_emaillinkrequest` | 3 | 3.853 |
| `core_outgoingemail` | 0 | 550 |
| `core_auditentry` | 0 | 1.100 |
| `procrastinate_jobs` | 0 | 550 |

## Resultats (mil·lisegons)

### Execució 1 (02:28, 3 min 43 s)
| Cas | n | Mitjana | Mediana | p10 | p90 | p95 | p99 |
|---|---|---|---|---|---|---|---|
| Adreça inexistent (referència) | 500 | 43,37 | 26,45 | 5,78 | 99,15 | 151,93 | 331,83 |
| Adreça inexistent (segona: soroll) | 500 | 45,92 | 28,21 | 5,95 | 108,66 | 155,75 | 316,81 |
| Compte personal actiu (correu a la cua) | 500 | 50,39 | 29,00 | 15,01 | 106,84 | 192,95 | 300,30 |
| Compte actiu limitat per destinatari | 500 | 51,58 | 29,56 | 9,88 | 107,82 | 167,24 | 451,70 |
| Compte personal pendent | 500 | 41,89 | 26,79 | 7,36 | 93,94 | 145,29 | 296,12 |
| Compte personal desactivat | 500 | 50,99 | 28,49 | 7,54 | 108,62 | 194,19 | 367,91 |
| Adreça de notificació d'un administrador | 500 | 43,78 | 27,22 | 5,69 | 97,29 | 159,15 | 324,50 |

| Diferència de medianes respecte a la referència | ms | IC 95 % (ms) |
|---|---|---|
| Adreça inexistent (soroll) | 1,76 | de 0,27 a 3,22 |
| Compte personal actiu | 2,55 | de 0,69 a 4,04 |
| Actiu limitat per destinatari | 3,11 | de 1,35 a 4,88 |
| Pendent | 0,34 | de -1,10 a 1,58 |
| Desactivat | 2,05 | de 0,45 a 3,91 |
| Administrador | 0,77 | de -0,53 a 2,01 |

### Execució 2 (02:33, 3 min 31 s)
| Cas | n | Mitjana | Mediana | p10 | p90 | p95 | p99 |
|---|---|---|---|---|---|---|---|
| Adreça inexistent (referència) | 500 | 33,92 | 24,37 | 5,84 | 74,34 | 117,67 | 227,12 |
| Adreça inexistent (segona: soroll) | 500 | 40,71 | 24,00 | 5,82 | 85,36 | 163,12 | 339,38 |
| Compte personal actiu (correu a la cua) | 500 | 55,23 | 28,81 | 16,34 | 107,09 | 145,09 | 323,84 |
| Compte actiu limitat per destinatari | 500 | 42,87 | 27,25 | 10,03 | 88,14 | 150,82 | 223,44 |
| Compte personal pendent | 500 | 38,07 | 25,30 | 7,61 | 86,02 | 108,39 | 249,86 |
| Compte personal desactivat | 500 | 38,14 | 24,29 | 7,56 | 87,93 | 141,84 | 217,46 |
| Adreça de notificació d'un administrador | 500 | 37,56 | 23,39 | 5,78 | 94,04 | 140,33 | 259,64 |

| Diferència de medianes respecte a la referència | ms | IC 95 % (ms) |
|---|---|---|
| Adreça inexistent (soroll) | -0,37 | de -2,29 a 1,84 |
| Compte personal actiu | 4,44 | de 2,49 a 7,94 |
| Actiu limitat per destinatari | 2,88 | de 0,81 a 5,28 |
| Pendent | 0,93 | de -0,85 a 3,06 |
| Desactivat | -0,08 | de -2,06 a 2,32 |
| Administrador | -0,98 | de -2,90 a 1,33 |

## Lectura
- **Amb la càrrega d'avui, la mediana no distingeix bé els casos.** Totes les medianes són 4 a 7 vegades les de la referència, i la cua llarga (p90 de 74 a 109 ms, p99 de 217 a 452 ms) ve de la competència per la CPU i pel PostgreSQL. A l'execució 1, fins i tot la diferència entre les dues adreces inexistents (soroll pur) surt amb un interval que no inclou el zero: amb aquesta càrrega, l'interval del bootstrap és massa optimista.
- **El p10 sí que separa els casos, igual a les dues execucions:** adreça inexistent i administrador, 5,7 a 5,9 ms; pendent i desactivat, 7,4 a 7,6 ms (es troba el compte i se'n bloqueja la fila); actiu limitat, uns 10 ms (a més, consulta els límits i escriu una entrada al registre); actiu amb correu, 15 a 16 ms (a més, genera el testimoni, renderitza la plantilla del correu, crea el correu i la tasca i escriu dues entrades). La diferència entre una adreça inexistent i un compte actiu és d'uns 9 a 10 ms, i a la referència era de 6,6 ms.
- La diferència existeix i es veu amb les dades d'avui, però no amb el mètode que el pla fixa per comparar (medianes amb l'interval del 95 %). El pla diu que, si el programa no reprodueix la diferència, no serveix per avaluar el canvi: aquestes xifres no s'han de fer servir com a «abans».

## Límits de la mesura
1. **Càrrega de la màquina** (el més important): altres sessions feien servir la CPU i el mateix PostgreSQL alhora. Cal repetir-la sense cap altra feina en marxa i documentar-ho.
2. **Només amb el worker aturat.** El pla demana també una execució amb el worker en marxa. No s'ha fet: la base de proves només existeix mentre dura la sessió de pytest, i el worker s'hi hauria de connectar des d'un altre procés. Es pot fer engegant `python manage.py procrastinate worker` amb la mateixa `DATABASE_URL` apuntant a `test_<base>` mentre corre la mesura, o amb una base de proves preparada a part.
3. **Dins del procés i sense xarxa.** No inclou el proxy, el TLS ni la xarxa, que poden amagar o ampliar la diferència. El pla demana repetir-la a l'entorn de proves, darrere del proxy amb HTTPS, abans de la decisió (c).
4. **Configuració de proves:** contrasenyes amb MD5 (no intervenen en aquesta petició) i correu en memòria (no s'envia res: el correu només es posa a la cua, com a producció).
5. **Windows i un PostgreSQL local**, no el VPS de producció. Els números absoluts no es poden traslladar; la comparació entre casos, sí.
6. **El bootstrap** remostreja blocs sencers, però no corregeix la deriva de la càrrega al llarg de l'execució.

## Què queda
- Tornar a executar el programa en condicions controlades (màquina sense cap altra feina, corrent connectada), amb el worker aturat i en marxa, i substituir els resultats d'aquest document si la mediana reprodueix la referència.
- La part (b) no s'ha començat i la (c) continua oberta (Q-086).
