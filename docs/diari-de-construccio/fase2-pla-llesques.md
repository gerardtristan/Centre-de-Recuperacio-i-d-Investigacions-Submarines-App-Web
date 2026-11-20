# Fase 2: pla de llesques F2-1 a F2-5 i retorn de la branca del 02

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 20/11/2026 18:45 | (vegeu la PR) | cap prova nova (només documentació) | [A comprovar] |

**En tres línies:** comença la fase 2 amb el proveïdor i el banc ficticis. El pla d'acceleració té ara cinc llesques verticals (llicència del soci, crear una sortida i inscriure-s'hi pagant, marge d'una activitat, material, ajuts i facturació), cadascuna amb una prova de flux sencer. La condició de la D6 ja es compleix i la branca del 02 torna en PR petites.

## Què s'ha fet
- Apartat nou «Fase 2 — llesques F2-1 a F2-5» al [pla d'acceleració](../plans/pla-acceleracio.md#fase-2-llesques): tasques per àncora del pla, sense dates ni còpia de les regles, i tres carrils de partida (06, port del 02, nucli de despeses del 09).
- [Estat del 02](../estat/M02.md): la condició de la D6 es compleix; com es porta la branca; files «per fer» del catàleg, la creació i els llocs. Fila nova al registre de la [089](../decisions/089-prova-d-acceleracio-interruptors-d1-a-d6.md).
- Les decisions 086, 087 i 088 de la branca aparcada són ara la [101](../decisions/101-el-cas-l-m02-05-es-fa-a-la-t-m02-04.md), la [102](../decisions/102-integracio-de-t-m00-i-t-m01-a-master.md) i la [103](../decisions/103-les-inscripcions-continuen-obertes-amb-les-places-plenes.md), amb les precisions que el responsable va acceptar el 12/11/2026 portades al pla (taula d'estats, P-M02-D pas 5, L-M02-05 i CA-M02-40).

## Decisions i perquè
- **101 a 103 i no 087 i 088:** a `master` la 087 i la 088 eren lliures, però el codi de la branca cita «086», «087» i «088». Amb números nous, qualsevol cita vella es veu de seguida que s'ha de corregir; amb la 087 i la 088 reaprofitades, una cita podria apuntar a una decisió diferent sense que ningú se n'adonés.
- **El nucli, coll d'ampolla:** cada mòdul declara els permisos al catàleg del nucli amb una migració de dades; aquestes PR van una darrere l'altra.

## Problemes trobats
- La branca del 02 té 11 commits fets després d'aparcar-la (34 en total). No es porten sencers: cada peça es torna a comprovar contra el pla en portar-la.

## Com se sap que funciona
- Enllaços i àncores comprovats; `tools/linia-cronologica/generate.py --ref HEAD` llegeix l'estat sense cap fila no vàlida.
