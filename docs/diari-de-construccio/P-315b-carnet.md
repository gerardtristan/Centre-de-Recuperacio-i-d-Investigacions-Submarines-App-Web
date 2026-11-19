# P-315b-carnet · Proves que confonien un número amb els microsegons d'una hora

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 20/11/2026 00:03 | 56a54306, 02a1b2cd | 4 ajustades | [A comprovar] |

**En tres línies:** el propietari va demanar tractar les proves que fallen de tant en tant com la P-315 ([T-DX-71](T-DX-71.md)): primer reproduir-les, després arreglar-les, mai saltar-les (19/11/2026). Aquesta és la primera que s'ha trobat al CI: `test_cards.py::test_own_valid_card_and_nothing_of_others` va fallar a master el 17/11 sense cap canvi que l'expliqués. Era un error de la prova, no del carnet.

## Què s'ha fet
- `apps/members/tests/test_cards.py`: la prova fixa el rellotge de l'etiqueta `{% now %}` en una hora amb «1999» als microsegons (com al CI), i busca el número de l'altre soci com a número sencer (`\b1999\b`), no com a quatre xifres seguides en qualsevol lloc de la pàgina.

## Decisions i perquè
- **La causa.** La prova crea un altre soci amb el número 1999 i comprova que «1999» no surti a la pàgina del carnet. La pàgina diu quan s'ha comprovat per última vegada amb `<time datetime="{% now 'c' %}">`, que porta els microsegons. El 17/11 l'hora era `14:29:59.119995`: «1999» hi era, i la prova fallava sense que el carnet ensenyés cap dada d'un altre soci. Passa aproximadament 3 vegades de cada 10.000 execucions.
- **Rellotge fixat a la prova, no a l'aplicació.** Amb el rellotge real, la condició depèn de l'atzar i la prova falla poques vegades. Amb el rellotge fixat, la condició es dona sempre: la prova antiga falla sempre i l'arreglada passa sempre.
- **Número sencer.** El número de soci a la pàgina va entre etiquetes o espais; dins d'una hora sempre té xifres al costat. La prova continua detectant el número de l'altre soci on sigui.
- **Cap prova saltada, sense reintents ni temps més llargs.**

## Problemes trobats
- **`test_rebut.py::test_rn_m05b_19` no és inestable.** El propietari la va posar d'exemple. Al CI (1.000 execucions, del 13 al 19/11/2026) només ha fallat a la branca de la T-DX-59 (18 i 19/11, sis proves alhora per un canvi de navegació, arreglat a 05714fa4) i a la seva pròpia branca el 13/11, mentre s'escrivia. En local, 40 execucions seguides en verd, 20 d'elles passada la mitjanit de Madrid (23 h UTC), l'hora en què fallen les proves que comparen dates UTC amb dates locals. No s'hi ha canviat res.
- **Les altres fallades del CI** són de branques en curs, arreglades amb el canvi següent de la mateixa branca, o ja arreglades a master: la P-315 (#264), la data del mandat a les 23 h UTC (`timezone.localdate`) i els fitxers estàtics avortats en canviar de pàgina (`STATIC_RESOURCE_TYPES`). Queda una altra prova inestable de causa diferent, que va en una PR a part (P-315b-xifrat).

## Com se sap que funciona
- Amb el rellotge fixat i la comprovació antiga, la prova falla amb el mateix missatge que al CI (`'1999' is contained here: 14:29:59.119995+01:00`).
- Amb l'arreglo: 20 passen, 20 vegades seguides; `test_cards.py`: 48 passen.
- Les tres proves de la segona tanda també fallen amb els microsegons forçats i la comprovació antiga, i passen 20 vegades seguides amb l'arreglo; `test_admissions_079.py` i `test_birth_date_035.py`: 42 passen.
- Cap altra prova de la suite compara un número amb el text sencer d'una pàgina que porti hores amb microsegons (revisades les comprovacions «"xifres" not in»).
- Ruff net.

## Evidències
- Sortida de proves · commit 56a54306 · executada el 20/11/2026 en local (PostgreSQL 16):
  ```
  $ pytest apps/members/tests/test_cards.py -q
  48 passed
  ```

## Comprovació §15.5
- Cap pantalla tocada: no calen captures ni axe.
