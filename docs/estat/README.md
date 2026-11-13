# Estat de les tasques

Mentre l'interruptor D1 de [`CLAUDE.md`](../../CLAUDE.md) sigui actiu (decisió [089](../decisions/089-prova-d-acceleracio-interruptors-d1-a-d6.md)), l'estat de les tasques s'apunta aquí i no a la fila de [`planning.md`](../planning.md). El pla diu què s'ha de fer; aquesta carpeta diu com està. La línia cronològica i la skill `propera-tasca` llegeixen l'estat d'aquí: si una tasca hi és, mana aquesta fila; si no hi és, val el que diu el pla.

- Un fitxer per mòdul: `M00.md` (amb les tasques T-RP i T-AJ), `M01.md`, `M04.md`, `M05a.md`…
- Una fila per tasca, amb cinc columnes: **tasca** (l'identificador primer), **estat**, **data** (`dd/mm/aaaa` o `—`), **PR** (`#12` o `—`) i **bloqueig o nota** (`—` si no n'hi ha).
- Quatre estats i cap més: **per fer**, **en curs**, **feta** i **bloquejada**. Una tasca bloquejada diu per què (una fila de [`pendents.md`](../decisions/pendents.md) o una altra tasca).
- La PR d'una tasca posa la seva fila a «feta»: quan la PR és a `master`, és veritat. Com que `master` està protegida, una PR fusionada sempre ha passat el CI i no cal anotar-ho.

## El que queda del format antic

- Les tasques del 00 i del 01 es van passar aquí el 13/11/2026 tal com les llegia la línia cronològica. Les que el pla donava per «feta en part» o «implementada, pendent de validació» hi consten com a **en curs**, amb el que queda a la nota. Partir-les en una part feta i una de bloquejada, cas per cas, encara no s'ha fet.
- L'historial de cada tasca antiga continua a la seva fila del pla, que ja no s'edita.
