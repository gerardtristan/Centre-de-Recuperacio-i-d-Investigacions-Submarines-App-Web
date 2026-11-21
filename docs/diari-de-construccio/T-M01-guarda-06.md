# Guarda del 01 · La fitxa del soci no corregeix les llicències que ja són al 06

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 21/11/2026 10:23 | f8411d52 | 11199 | [A comprovar] |

**En tres línies:** quan les llicències de les fitxes dels socis passin al mòdul de llicències, la secretaria ja no les podrà corregir des de la fitxa, sinó des del mòdul de llicències. Fins ara la fitxa deixava fer-ho, i l'endemà la comprovació diària tornava a posar el que diu el 06, de manera que el canvi es perdia sense avisar. Ara la fitxa diu «Al mòdul de llicències».

## Què s'ha fet
- `members.licences.correct_record` rebutja un registre amb `licence_ref`. La pàgina de correcció respon «no trobat» i la fitxa no hi enllaça. Regla: [P-M06-H, pas 3](../planning.md#M06-5-processos), decisió 052.

## Decisions i perquè
- «No trobat» a la pàgina (com un registre d'un altre soci), més la guarda al servei, que és el control.

## Problemes trobats
- Cap destacable. Primer la prova (`apps/members/tests/test_licence_in_06.py`), que fallava.

## Com se sap que funciona
El servei i la pàgina rebutgen el registre lligat, i la fitxa no hi enllaça. La resta de proves de la fitxa continuen en verd.

## Evidències
- Sortida de proves · commit f8411d52 · executada el 21/11/2026 en local (PostgreSQL 16): 11199 passed (sense la prova de navegació que falla en local també a master). Sense captura: el canvi només es veu amb un registre lligat al 06.
