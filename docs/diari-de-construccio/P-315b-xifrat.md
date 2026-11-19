# P-315b-xifrat · L'escaneig de dades personals que trobava un nom dins d'un text xifrat

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 20/11/2026 00:09 | 25e2faa8 | 1 nova | [A comprovar] |

**En tres línies:** el propietari va demanar tractar les proves que fallen de tant en tant com la P-315 ([T-DX-71](T-DX-71.md)): primer reproduir-les, després arreglar-les, mai saltar-les (19/11/2026). El 16/11, la prova de les dades bloquejades (`test_locked_data.py::test_ca_19_5…`) va fallar al CI dient que el nom «Anna» seguia a la base de dades, dins del secret xifrat d'un doble factor. Era un error de la prova: el nom hi havia sortit per casualitat.

## Què s'ha fet
- `apps/members/tests/test_privacy.py`: `leaks()`, l'eina de les proves que recorre totes les taules buscant dades personals que haurien d'haver desaparegut, ja no mira els camps xifrats (`*_encrypted`), les empremtes de contrasenya (`password`) ni les sessions (`session_key`, `session_data`).
- Prova nova que força la casualitat: `test_leaks_does_not_count_a_name_that_comes_out_by_chance_in_a_random_value` posa «Anna» dins del secret xifrat i de l'empremta de la contrasenya d'un compte, i comprova que `leaks()` no ho compta però sí que troba el nom en clar.

## Decisions i perquè
- **La causa.** Un text xifrat o una empremta de contrasenya són lletres i xifres a l'atzar. `leaks()` hi buscava el nom sense distingir majúscules, i un nom de quatre lletres com «Anna» hi surt aproximadament una vegada de cada 10.000 valors. Ho fan servir les proves de l'esborrat (RGPD) i de les dades bloquejades, i cadascuna crea comptes amb doble factor.
- **Treure aquests camps de l'escaneig, no canviar el nom de la prova.** Amb un altre nom passaria igual, només amb una altra probabilitat. Aquests camps no poden guardar res en clar: si una dada personal hi fos llegible, el xifratge ja estaria trencat, i això ho proven les proves del xifratge.
- **La prova força la casualitat.** Amb valors xifrats de veritat, que hi surti el nom depèn de l'atzar. Amb el valor posat a mà, la prova falla sempre sense l'arreglo i passa sempre amb l'arreglo.
- **Cap prova saltada, sense reintents ni temps més llargs.**

## Problemes trobats
- Cap més. La recerca de proves inestables (1.000 execucions del CI, del 13 al 19/11/2026) és al diari de la [P-315b-carnet](P-315b-carnet.md).

## Com se sap que funciona
- La prova nova falla sense l'arreglo (`accounts.Account.password #1: nom` i `accounts.TotpDevice.secret_encrypted`) i passa amb l'arreglo, 20 vegades seguides.
- `test_privacy.py` i `test_locked_data.py`: 50 passen; les dues proves de les dades bloquejades que fan servir `leaks()`, 20 vegades seguides cadascuna en verd.
- Ruff net.

## Evidències
- Sortida de proves · commit 25e2faa8 · executada el 20/11/2026 en local (PostgreSQL 16):
  ```
  $ pytest apps/members/tests/test_privacy.py apps/core/tests/test_locked_data.py -q
  50 passed
  ```

## Comprovació §15.5
- Cap pantalla tocada: no calen captures ni axe.
