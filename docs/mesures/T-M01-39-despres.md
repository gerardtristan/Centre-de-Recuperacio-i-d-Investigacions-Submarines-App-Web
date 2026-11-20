# T-M01-39, part (a): mesura després del canvi (T-M01-39b)

Mateix programa i mateix mètode que la [mesura d'abans](T-M01-39-abans.md), **després** de la part (b): la petició de «He oblidat la contrasenya» desa una fila «pendent» amb l'empremta de l'adreça i posa una tasca a la cua, sense buscar el compte.

## Resum en tres línies
- **Cap cas no es distingeix de les adreces inexistents:** totes les diferències de medianes respecte a la primera adreça inexistent són de -0,06 a +0,05 ms, amb intervals del 95 % que inclouen el zero, i els p10–p90 es solapen (de 4,4 a 6,3 ms en tots els casos).
- Abans, el compte actiu era 6,2 ms més lent i l'actiu limitat, el pendent i el desactivat, d'1,1 a 2,7 ms: totes aquestes diferències han desaparegut.
- Ara totes les peticions costen com una adreça inexistent d'abans (mediana de 5,0 a 5,1 ms). És evidència útil, no prova absoluta (pla, part a): amb més mostres es podrien detectar diferències més petites, i falta repetir-la darrere del proxy (part c, Q-086).

## Entorn
| | |
|---|---|
| Data i hora | 20/11/2026, 04:28:21 (execució 1) i 04:29:40 (execució 2), CET |
| Commit | `97d80ec6` (T-M01-39b) |
| Programari, màquina, configuració i base | els mateixos que la mesura d'abans del 20/11/2026 |
| Worker | aturat: les tasques es queden a la cua (el programa ho comprova) |
| Comprovacions del programa | resposta idèntica en tots els casos; cap correu a la petició; una fila pendent i una tasca per petició (3.850); cap limitada per origen |

Files: `accounts_emaillinkrequest` 3 → 3.853, `procrastinate_jobs` 0 → 3.850, `core_outgoingemail` i `core_auditentry` 0 → 0 (la petició ja no envia res ni escriu al registre).

## Resultats (mil·lisegons)

### Execució 1 (04:28)
| Cas | n | Mitjana | Mediana | p10 | p90 | p95 | p99 |
|---|---|---|---|---|---|---|---|
| Adreça inexistent (referència) | 500 | 5,42 | 5,02 | 4,47 | 6,27 | 6,80 | 7,68 |
| Adreça inexistent (segona: soroll) | 500 | 5,17 | 4,98 | 4,46 | 6,02 | 6,53 | 8,47 |
| Compte personal actiu (correu posat a la cua) | 500 | 5,29 | 5,03 | 4,47 | 6,09 | 6,52 | 8,31 |
| Compte actiu limitat per destinatari | 500 | 5,47 | 4,98 | 4,44 | 6,17 | 6,71 | 7,95 |
| Compte personal pendent | 500 | 5,24 | 5,01 | 4,44 | 6,03 | 6,73 | 8,00 |
| Compte personal desactivat | 500 | 5,20 | 5,03 | 4,41 | 6,12 | 6,50 | 8,66 |
| Adreça de notificació d'un compte d'administrador | 500 | 5,21 | 5,06 | 4,45 | 6,11 | 6,70 | 7,77 |

| Cas | Diferència (ms) | Interval de confiança del 95 % (ms) |
|---|---|---|
| Adreça inexistent (segona: soroll) | -0,04 | de -0,11 a 0,06 |
| Compte personal actiu (correu posat a la cua) | 0,02 | de -0,07 a 0,09 |
| Compte actiu limitat per destinatari | -0,04 | de -0,12 a 0,04 |
| Compte personal pendent | -0,01 | de -0,08 a 0,07 |
| Compte personal desactivat | 0,01 | de -0,07 a 0,08 |
| Adreça de notificació d'un compte d'administrador | 0,05 | de -0,04 a 0,13 |

### Execució 2 (04:29)
| Cas | n | Mitjana | Mediana | p10 | p90 | p95 | p99 |
|---|---|---|---|---|---|---|---|
| Adreça inexistent (referència) | 500 | 5,37 | 5,11 | 4,52 | 6,01 | 6,47 | 7,68 |
| Adreça inexistent (segona: soroll) | 500 | 5,73 | 5,11 | 4,48 | 6,21 | 6,91 | 9,65 |
| Compte personal actiu (correu posat a la cua) | 500 | 5,47 | 5,11 | 4,45 | 6,28 | 6,76 | 9,81 |
| Compte actiu limitat per destinatari | 500 | 5,28 | 5,12 | 4,48 | 6,32 | 6,73 | 7,98 |
| Compte personal pendent | 500 | 5,33 | 5,05 | 4,49 | 6,10 | 6,55 | 8,42 |
| Compte personal desactivat | 500 | 5,27 | 5,09 | 4,48 | 6,22 | 6,69 | 8,47 |
| Adreça de notificació d'un compte d'administrador | 500 | 5,51 | 5,09 | 4,46 | 6,29 | 6,95 | 9,77 |

| Cas | Diferència (ms) | Interval de confiança del 95 % (ms) |
|---|---|---|
| Adreça inexistent (segona: soroll) | 0,00 | de -0,07 a 0,08 |
| Compte personal actiu (correu posat a la cua) | 0,00 | de -0,06 a 0,08 |
| Compte actiu limitat per destinatari | 0,02 | de -0,05 a 0,11 |
| Compte personal pendent | -0,06 | de -0,12 a 0,03 |
| Compte personal desactivat | -0,02 | de -0,07 a 0,06 |
| Adreça de notificació d'un compte d'administrador | -0,01 | de -0,06 a 0,08 |

## Límits
- Els mateixos que la mesura d'abans (sense worker, dins del procés, Windows local).
- La feina que abans feia la petició ara la fa la tasca: el temps de la tasca no es veu des de fora, però el correu arriba més tard (normalment segons; com a màxim, el retard de 5 minuts de la Q-085).
