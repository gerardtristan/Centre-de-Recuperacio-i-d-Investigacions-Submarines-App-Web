# T-M01-39, part (a): mesura abans del canvi

Temps de resposta de «He oblidat la contrasenya» (`POST /compte/contrasenya/oblidada/`, vista `password_reset_request_view`) segons el cas de l'adreça escrita, **abans** de la part (b) (la cua, T-M01-39b). Protocol: secció «T-M01-39 en detall», part (a), del pla. La mesura de després és de la T-M01-39b, en un document a part (`T-M01-39-despres.md`).

## Resum en tres línies
- **El 20/11/2026, sense la càrrega de l'11/11, el programa reprodueix la referència del 03/11/2026:** mediana de 4,9 a 5,0 ms per a una adreça inexistent i d'11,1 a 11,3 ms per a un compte actiu amb correu (la referència deia 3,9 i 10,5); la diferència és de 6,2 a 6,3 ms (la referència, 6,6).
- El soroll entre les dues adreces inexistents és de 0,0 ms (interval de -0,08 a 0,06), i tots els altres casos se'n separen amb intervals que no inclouen el zero: pendent i desactivat, +1,1 ms; actiu limitat, +2,7 ms; actiu, +6,2 ms. L'adreça d'un administrador no se'n distingeix (no és un compte personal).
- Segons el criteri del pla, **aquestes dues execucions serveixen d'«abans»**. Les de l'11/11/2026 (màquina carregada) es conserven a sota, però no valen.

## Programa
`tools/mesura_recuperacio.py`. És una eina de desenvolupament, fora de la suite i del CI: `pytest` sense arguments només recull `apps/` (`testpaths` de `pyproject.toml`). És un mòdul de pytest perquè és pytest qui crea la base de proves (`test_<base>`) i hi aplica les migracions: no toca mai la base de desenvolupament ni cap base real.

    pytest tools/mesura_recuperacio.py -s -p no:cacheprovider --log-level=WARNING

Les execucions d'aquest document són al commit `db36220b` (abans de la T-M01-39b), amb el programa tal com era aleshores (comprovava un correu per bloc). El mètode és el mateix que a l'11/11.

## Mètode
- **Què es mesura.** Un `POST` amb el client de proves de Django, dins del mateix procés: tota la pila de l'aplicació (middleware, formulari, servei `email_links.request_password_reset`, consultes, registre d'activitat, posar el correu a la cua) i la confirmació real de la transacció. No inclou la xarxa, el TLS ni el proxy. Rellotge: `time.perf_counter_ns`.
- **Dades confirmades.** `CommittedDataTestCase`: les dades es confirmen de debò, perquè el cost del `COMMIT` hi compti, i s'esborren en acabar. Només dades inventades (`@example.org`, «Mesura Inventada»).
- **Casos (7 per bloc, en ordre aleatori amb la llavor 1954):** dues adreces inexistents (la diferència entre totes dues és el soroll), compte personal actiu (rep el correu), actiu limitat per destinatari (tres enllaços enviats l'última hora), pendent, desactivat i l'adreça de notificació d'un compte d'administrador.
- **Sense interferències dels límits.** Cada petició porta una IP diferent (`REMOTE_ADDR`, amb `NUM_PROXIES=0`) i cada bloc té un compte actiu nou i dues adreces inexistents noves.
- **Blocs:** 50 d'escalfament descartats i 500 de mesurats (3.850 peticions per execució).
- **Estadística per cas:** n, mitjana, mediana, p10, p90, p95 i p99. Diferència de medianes respecte a la primera adreça inexistent amb un interval de confiança del 95 % per bootstrap (2.000 remostrejos de blocs sencers, perquè els set casos d'un bloc s'han mesurat junts).
- **Comprovacions que invaliden la mesura si fallen:** la resposta és idèntica en tots els casos (llevat del testimoni CSRF de la plantilla base); hi ha exactament un correu per bloc, el del compte actiu; cap correu no ha sortit de la cua; hi ha una petició limitada per destinatari per bloc i cap de limitada per origen. Totes dues execucions les han passades.

## Entorn (20/11/2026)
| | |
|---|---|
| Data i hora | 20/11/2026, 04:15:56 (execució 1) i 04:17:47 (execució 2), CET; uns 30 s de mesura cadascuna |
| Commit | `db36220b` (master, abans de la T-M01-39b) |
| Programari | Python 3.12.10, Django 5.2.18, PostgreSQL 16.15, Windows 11 (AMD64) |
| Màquina | la mateixa de l'11/11 (Intel Core i5-8400, 15,9 GB, sobretaula connectat a la corrent) |
| Configuració | `config.settings.test` |
| Base de dades | `test_night_m0139a`, nova a cada execució, al PostgreSQL local |
| Worker | aturat: cap tasca d'enviament no s'ha executat durant la mesura |
| Altres processos | **càrrega baixa**: just abans de començar, 6 processos de Python en marxa i la CPU al 25 %. No es pot garantir que cap altra sessió no hagi fet servir la màquina durant la mesura; la cua curta (p99 de 6,4 a 14,8 ms) diu que no hi ha hagut competència apreciable |

Files de les taules implicades (iguals a les dues execucions): `core_person` 4 → 554, `accounts_account` 4 → 554, `accounts_emaillinkrequest` 3 → 3.853, `core_outgoingemail` 0 → 550, `core_auditentry` 0 → 1.100, `procrastinate_jobs` 0 → 550.

## Resultats (mil·lisegons)

### Execució 1 (04:15)
| Cas | n | Mitjana | Mediana | p10 | p90 | p95 | p99 |
|---|---|---|---|---|---|---|---|
| Adreça inexistent (referència) | 500 | 5,56 | 4,99 | 4,57 | 5,82 | 6,13 | 6,75 |
| Adreça inexistent (segona: soroll) | 500 | 5,52 | 5,00 | 4,58 | 5,80 | 6,08 | 7,01 |
| Compte personal actiu (correu posat a la cua) | 500 | 11,82 | 11,29 | 10,48 | 13,04 | 13,57 | 14,76 |
| Compte actiu limitat per destinatari | 500 | 8,04 | 7,72 | 7,19 | 8,93 | 9,37 | 10,26 |
| Compte personal pendent | 500 | 6,32 | 6,14 | 5,64 | 7,16 | 7,55 | 8,41 |
| Compte personal desactivat | 500 | 6,28 | 6,19 | 5,65 | 7,02 | 7,27 | 7,80 |
| Adreça de notificació d'un compte d'administrador | 500 | 5,32 | 4,96 | 4,58 | 5,74 | 6,03 | 6,59 |

| Cas | Diferència (ms) | Interval de confiança del 95 % (ms) |
|---|---|---|
| Adreça inexistent (segona: soroll) | 0,01 | de -0,06 a 0,06 |
| Compte personal actiu (correu posat a la cua) | 6,30 | de 6,24 a 6,42 |
| Compte actiu limitat per destinatari | 2,73 | de 2,67 a 2,81 |
| Compte personal pendent | 1,16 | de 1,08 a 1,23 |
| Compte personal desactivat | 1,21 | de 1,12 a 1,28 |
| Adreça de notificació d'un compte d'administrador | -0,03 | de -0,08 a 0,04 |

### Execució 2 (04:17)
| Cas | n | Mitjana | Mediana | p10 | p90 | p95 | p99 |
|---|---|---|---|---|---|---|---|
| Adreça inexistent (referència) | 500 | 5,38 | 4,94 | 4,53 | 5,73 | 6,11 | 6,84 |
| Adreça inexistent (segona: soroll) | 500 | 5,06 | 4,92 | 4,53 | 5,73 | 5,97 | 6,43 |
| Compte personal actiu (correu posat a la cua) | 500 | 11,51 | 11,14 | 10,44 | 12,78 | 13,35 | 14,44 |
| Compte actiu limitat per destinatari | 500 | 8,04 | 7,65 | 7,10 | 8,92 | 9,31 | 10,20 |
| Compte personal pendent | 500 | 6,20 | 6,04 | 5,60 | 7,03 | 7,26 | 7,89 |
| Compte personal desactivat | 500 | 6,20 | 6,06 | 5,61 | 7,02 | 7,28 | 7,93 |
| Adreça de notificació d'un compte d'administrador | 500 | 5,26 | 4,93 | 4,53 | 5,74 | 6,05 | 6,73 |

| Cas | Diferència (ms) | Interval de confiança del 95 % (ms) |
|---|---|---|
| Adreça inexistent (segona: soroll) | -0,03 | de -0,08 a 0,04 |
| Compte personal actiu (correu posat a la cua) | 6,20 | de 6,12 a 6,30 |
| Compte actiu limitat per destinatari | 2,70 | de 2,65 a 2,77 |
| Compte personal pendent | 1,10 | de 1,04 a 1,17 |
| Compte personal desactivat | 1,12 | de 1,06 a 1,19 |
| Adreça de notificació d'un compte d'administrador | -0,02 | de -0,07 a 0,04 |

## Límits
- Només amb el worker aturat. Amb el worker en marxa no s'ha pogut fer: la base de proves només existeix mentre dura la sessió de pytest i l'eina de proves nocturnes no deixa connectar-hi un altre procés. Amb la cua de la (b) el worker no intervé en la petició.
- Dins del procés, sense xarxa ni proxy: la repetició darrere del proxy amb HTTPS és de la (c) (Q-086).
- Windows i un PostgreSQL local: els números absoluts no es poden traslladar al VPS; la comparació entre casos, sí.

## Mesura de l'11/11/2026 (no val: màquina carregada)
### Entorn de l'11/11/2026
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

### Resultats (mil·lisegons)

#### Execució 1 (02:28, 3 min 43 s)
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

#### Execució 2 (02:33, 3 min 31 s)
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

### Lectura
- **Amb la càrrega d'avui, la mediana no distingeix bé els casos.** Totes les medianes són 4 a 7 vegades les de la referència, i la cua llarga (p90 de 74 a 109 ms, p99 de 217 a 452 ms) ve de la competència per la CPU i pel PostgreSQL. A l'execució 1, fins i tot la diferència entre les dues adreces inexistents (soroll pur) surt amb un interval que no inclou el zero: amb aquesta càrrega, l'interval del bootstrap és massa optimista.
- **El p10 sí que separa els casos, igual a les dues execucions:** adreça inexistent i administrador, 5,7 a 5,9 ms; pendent i desactivat, 7,4 a 7,6 ms (es troba el compte i se'n bloqueja la fila); actiu limitat, uns 10 ms (a més, consulta els límits i escriu una entrada al registre); actiu amb correu, 15 a 16 ms (a més, genera el testimoni, renderitza la plantilla del correu, crea el correu i la tasca i escriu dues entrades). La diferència entre una adreça inexistent i un compte actiu és d'uns 9 a 10 ms, i a la referència era de 6,6 ms.
- La diferència existeix i es veu amb les dades d'avui, però no amb el mètode que el pla fixa per comparar (medianes amb l'interval del 95 %). El pla diu que, si el programa no reprodueix la diferència, no serveix per avaluar el canvi: aquestes xifres no s'han de fer servir com a «abans».

### Límits de la mesura
1. **Càrrega de la màquina** (el més important): altres sessions feien servir la CPU i el mateix PostgreSQL alhora. Cal repetir-la sense cap altra feina en marxa i documentar-ho.
2. **Només amb el worker aturat.** El pla demana també una execució amb el worker en marxa. No s'ha fet: la base de proves només existeix mentre dura la sessió de pytest, i el worker s'hi hauria de connectar des d'un altre procés. Es pot fer engegant `python manage.py procrastinate worker` amb la mateixa `DATABASE_URL` apuntant a `test_<base>` mentre corre la mesura, o amb una base de proves preparada a part.
3. **Dins del procés i sense xarxa.** No inclou el proxy, el TLS ni la xarxa, que poden amagar o ampliar la diferència. El pla demana repetir-la a l'entorn de proves, darrere del proxy amb HTTPS, abans de la decisió (c).
4. **Configuració de proves:** contrasenyes amb MD5 (no intervenen en aquesta petició) i correu en memòria (no s'envia res: el correu només es posa a la cua, com a producció).
5. **Windows i un PostgreSQL local**, no el VPS de producció. Els números absoluts no es poden traslladar; la comparació entre casos, sí.
6. **El bootstrap** remostreja blocs sencers, però no corregeix la deriva de la càrrega al llarg de l'execució.
