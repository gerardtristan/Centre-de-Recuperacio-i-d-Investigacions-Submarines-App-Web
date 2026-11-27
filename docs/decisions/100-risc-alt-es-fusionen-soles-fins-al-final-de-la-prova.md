# 100. Fins al final de la prova (27/11/2026), una PR `risc:alt` es fusiona sola amb condicions, amb excepcions que continuen esperant el sí del propietari

- **Data:** 19/11/2026
- **Estat:** Acceptada (propietari, instrucció escrita del 19/11/2026). **Val des del 19/11/2026 a les 21:58**, quan el propietari la va escriure, i no des que aquesta PR entra a `master`. El 20/11/2026 el propietari ho va precisar: «des del 19/11 a les 21:58 ja no cal el meu "fusiona la #N": si el CI és verd, fusiona tu mateix també les risc:alt i informa-me'n al resum D4». Temporal: s'acaba el 27/11/2026.
- **Pròrroga (27/11/2026):** el propietari l'allarga, amb les mateixes condicions i excepcions, fins al final de la fase 2, com la prova de la [089](089-prova-d-acceleracio-interruptors-d1-a-d6.md) (registre d'estat de la 089). Llavors ho torna a decidir; si no diu res, la regla torna a la 098 (punt 5). On aquesta decisió diu «27/11/2026», val «el final de la fase 2».
- **Canvia:** el punt 1 de la [098](098-risc-alt-nomes-amb-el-si-escrit-del-propietari.md) i la D4 del `CLAUDE.md` ([089](089-prova-d-acceleracio-interruptors-d1-a-d6.md)), fins al 27/11/2026. La resta de la 098 continua vigent, i la 098 sencera val per a les excepcions del punt 2.

## Context

Amb la 098, cada `risc:alt` espera un «fusiona la #N» del propietari. Per acabar la fase 1 amb integracions fictícies ([092](092-carril-extern-amb-proveidor-i-banc-ficticis.md)) abans del final de la prova, el propietari vol que les `risc:alt` que no toquen res real es fusionin soles, i guardar el seu sí per al que no es pot desfer o rebaixa els controls.

## Decisió

1. **Des del 19/11/2026 a les 21:58 i fins al 27/11/2026, una PR `risc:alt` es fusiona sola, sense el «fusiona la #N» del propietari,** quan té: el CI verd, la branca al dia amb `master`, la revisió automàtica sense res pendent, les proves i les captures mirades, i l'entrada al diari de construcció.
2. **Continuen esperant el sí escrit del propietari amb el número de la PR** (la 098 hi segueix valent):
   - qualsevol PR que encengui res a producció, permeti cobraments reals o dades reals de socis, o canviï `PAYMENTS_LIVE_CHARGES_ALLOWED`, `CLUBER_FINAL_IMPORT_ALLOWED` o qualsevol interruptor apagat a producció per la D2;
   - canvis al `CLAUDE.md`, als interruptors D1 a D6 o a aquesta mateixa regla;
   - canvis al CI que en rebaixin el control: baixar el llindar de cobertura, treure o saltar proves, treure gitleaks o el lint;
   - secrets, claus i xifratge ([044](044-domiciliacio-sepa-iban-i-mandat-xifrats.md) i [051](051-abast-de-la-044-i-documents-de-justificacio.md)).
3. **Resum D4:** cada `risc:alt` fusionada sola hi surt a l'apartat «risc:alt fusionades sense el propietari», amb una línia del que toca de diners, permisos o dades personals.
4. **Si el propietari hi troba res**, es corregeix amb una PR nova; no es reescriu la història.
5. **El 27/11/2026 la regla torna a la 098**, tret que el propietari digui el contrari.
6. **No cal esperar que aquesta PR sigui a `master`:** la regla val des del 19/11/2026 a les 21:58 (precisió del propietari del 20/11/2026).

## Conseqüències

- Aquesta PR toca el `CLAUDE.md` i la va autoritzar el propietari per escrit («fusiona la #277»).
- Les risc:baix i risc:mitja continuen com diu la [094](094-fusio-de-les-risc-alt-i-tres-carrils.md).
- El 27/11/2026, si el propietari no diu res, una PR nova torna la D4 al text de la 098 i afegeix la fila al registre d'estat de la 089.

## Font

Instrucció escrita del propietari, 19/11/2026 («Prompt del propietari (19/11/2026), per al PILOT», part A).
