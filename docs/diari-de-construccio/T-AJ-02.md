# T-AJ-02 · Pantalla base d'ajustos i permís de dos nivells per apartat

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 16/11/2026 12:20 | 93d3465, a3d8934 (PR #48) | 18 noves, 2 canviades i 1 al navegador | verd a 7c4842b (execució 43852237712) |

**En tres línies:** l'administració té ara un apartat «Ajustos» on es veuen i es canvien els valors de negoci (terminis, dies, imports) sense tocar el codi. Cada valor mostra el que val ara, el que valdrà si hi ha un canvi programat, el valor inicial, el rang permès i l'historial de canvis. Qui només el pot consultar el veu, però no el pot canviar, i si ho intenta queda apuntat.

## Què s'ha fet
- Una sola pantalla per a tots els mòduls (`/gestio/ajustos/<apartat>/`): l'apartat és el mòdul de l'ajust. Detall: [peça comuna d'ajustos](../planning.md#valors-configurables-055), RN-AJ-05.
- Formulari segons el tipus (enter, euros, sí o no, opció, dia i mes, llista, text) i historial amb qui, quan, l'anterior, el nou, la data d'entrada en vigor i la nota (CA-AJ-05).
- Dos nivells per apartat ([RN-RP-22](../planning.md#rols-i-permisos-059)): «Cons.» veu, «Sí» edita tots els valors; `settings.edit.<clau>` edita un sol valor i demana l'apartat (RN-RP-03).
- Catàleg: l'apartat de pagaments i l'edició dels dos valors de VC-17, amb la configuració inicial (tresorer i administrador, «Cons.»; editar, només l'administrador).
- Entrada «Ajustos» al menú, només amb algun permís d'apartat.

## Decisions i perquè
- **Una pantalla per a tots els apartats**, en lloc d'una per mòdul: cada mòdul només hi posa les seves claus (migració) i els seus permisos (catàleg). La pantalla de pagaments és aquesta mateixa amb l'apartat `payments`.
- **El rebuig queda al registre fora de la transacció** del canvi: si no, en tornar «no trobat» es desfaria.
- **La migració de les cel·les inicials va amb el catàleg** (al nucli) i no amb els ajustos del 05b: les proves de la matriu demanen que cada cel·la del catàleg tingui la seva fila des del mateix canvi.
- **L'etiqueta de cada valor** és la descripció del seu permís d'edició al catàleg: `Setting` no té cap camp d'etiqueta al pla.

## Problemes trobats
- La primera versió de la vista passava de les 400 línies de codi d'aplicació de la PR (D4): s'ha compactat el formulari en una sola classe.
- Els imports en euros s'escriuen amb coma: el camp decimal ha de ser localitzat.
- La revisió automàtica (PR #48) va trobar que el menú fallava (KeyError) si el catàleg no tenia cap apartat d'ajustos: prova que ho reprodueix i arreglo. També: el rebuig té un servei propi (`deny`) i `change` calcula els permisos una sola vegada.

## Com se sap que funciona
- CA-AJ-01 (fora de rang, «No s'ha desat res.» i cap versió), CA-AJ-02 (sense apartat, «no trobat» a les tres rutes; amb només «Cons.», «no trobat» i entrada al registre), CA-AJ-05 (historial a la pantalla).
- RN-RP-22 i RN-RP-03: l'apartat amb «Sí» edita tots els valors; el permís d'un valor no n'edita cap altre; sense l'apartat, el permís d'un valor no hi val.
- Les proves per cel·la del catàleg (CA-RP-13) inclouen les tres files noves.
- Al navegador: l'administrador entra per «Ajustos», desa un valor fora de rang (rebutjat) i un de vàlid; el tresorer el veu sense formulari. A 1280, 390 i 320 px, en clar i en fosc.

## Evidències
- Captura: `captures/2026-11-16_1115_T-AJ-02_valor-desat.png`
  *16/11/2026 11:15 (Europa/Madrid) · local, dades inventades (prova e2e) · commit 93d3465*
- Sortida de proves · commit 93d3465 · executada el 16/11/2026 en local (PostgreSQL 16):
  ```
  $ pytest -q
  4674 passed, 51 deselected
  $ pytest -q -m e2e apps/core/tests/e2e/test_ajustos.py apps/core/tests/e2e/test_navegacio.py
  3 passed
  ```

## Termes nous
- **Apartat d'ajustos:** el grup de valors d'un mòdul (per exemple, «Ajustos de pagaments»), amb un sol permís per veure'l o editar-lo sencer.
