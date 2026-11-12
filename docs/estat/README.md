# Estat de les tasques

Mentre l'interruptor D1 de [`CLAUDE.md`](../../CLAUDE.md) sigui actiu (decisió [089](../decisions/089-prova-d-acceleracio-interruptors-d1-a-d6.md)), l'estat de les tasques **començades després de la congelació** s'apunta aquí i no a la fila de [`planning.md`](../planning.md). El pla diu què s'ha de fer; aquesta carpeta diu com està.

- Un fitxer per mòdul: `M04.md`, `M05a.md`, `M05b.md`…
- Una línia per tasca, amb aquestes columnes: tasca, estat, PR i bloqueig o nota.
- Quatre estats i cap més: **per fer**, **en curs**, **feta** i **bloquejada**. Una tasca bloquejada diu per què (una fila de [`pendents.md`](../decisions/pendents.md) o una altra tasca). Una tasca que té una part feta i una de bloquejada es parteix en dues.
- Una tasca és «feta» quan la seva PR és a `master`. Com que `master` està protegida, una PR fusionada sempre ha passat el CI: no cal anotar-ho.

## El que encara no s'ha mogut

- Les tasques del 00 i del 01 anteriors al 13/11/2026 continuen tenint l'estat a la seva fila del pla. Passar-les aquí és la tasca 4 del [pla d'acceleració](../plans/pla-acceleracio.md).
- La skill `propera-tasca` i la línia cronològica encara llegeixen l'estat de les files del pla: les tasques apuntades aquí no hi surten fins que s'adaptin.
