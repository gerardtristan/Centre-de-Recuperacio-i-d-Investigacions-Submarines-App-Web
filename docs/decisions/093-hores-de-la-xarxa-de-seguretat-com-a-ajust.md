# 093. Hores de la xarxa de seguretat abans de deixar un intent a revisar, com a ajust

- **Data:** 16/11/2026
- **Estat:** Acceptada (propietari, 16/11/2026; instrucció escrita). El text del propietari: «`SAFETY_NET_GIVE_UP` ha de passar a ajust (norma: tot valor i temps configurable). Afegeix-la a VC-17 i a la pantalla d'ajustos de pagaments com a tasca nova; és risc:alt i la revisaré jo.»
- **Origen:** la norma de valors i llistes de negoci de `CLAUDE.md` (cap valor de negoci escrit al codi; [055](055-ajustos-configurables-i-addendes.md)) i la nota `shortcut:` que la T-M05b-22 va deixar a `apps/payments/processing.py`.

## Context

La xarxa de seguretat del 05b passa un cop al dia i consulta al proveïdor les ordres en curs sense notificació ([L-M05b-01](../planning.md#M05b-9-criteris)). Si no pot consultar o tancar una ordre, la torna a provar l'endemà i, passades 24 hores des que va començar l'intent, el deixa «a revisar» perquè el tresorer el vegi. Les 24 hores són una constant del codi (`SAFETY_NET_GIVE_UP`) que no és a VC-17, i la T-M05b-22 (PR #49) no la va convertir en ajust perquè calia decidir-ho abans.

El 05b és congelat ([089](089-prova-d-acceleracio-interruptors-d1-a-d6.md), D1): una regla seva només es canvia amb una decisió numerada i una sola edició al lloc de la regla, en una PR `risc:alt`.

## Decisió

1. **VC-17 té un tercer valor**, `payments.safety_net_give_up_hours`: les hores des que comença un intent que la xarxa de seguretat el torna a provar abans de deixar-lo «a revisar». Valor inicial **24**, el que fa servir el codi avui.
2. **Rang proposat: 24 a 168 hores.** La xarxa passa un cop al dia: per sota de 24, un sol reintent fallat ja aniria a revisar; 168 hores és una setmana. El rang és un dubte configurable (089, D2) i és a la [P-102](pendents.md) amb aquesta proposta com a opció per defecte.
3. **No afecta diners** (no canvia cap import: només quan un intent passa a la llista «a revisar») i **no té data d'entrada en vigor**: el valor nou s'aplica a la passada següent de la xarxa.
4. **L'edita només l'Administrador**, com la resta de VC-17 (permís `settings.edit.payments.safety_net_give_up_hours`, AJ5b-3, sota l'apartat `settings.section.payments`; RN-RP-22). El tresorer el veu.
5. La feina és una tasca nova, la **T-M05b-28**.

L'edició del pla és una sola: un bloc nou al final de l'[addenda de la 055 del 05b](../planning.md#M05b-addenda-055), amb el valor, la regla RN-M05b-31, el criteri CA-M05b-33 i la fila de la T-M05b-28. On el bloc i l'[apèndix de valors configurables](../planning.md#valors-configurables) no coincideixen per a VC-17, val el bloc.

## Conseqüències

- Cap comportament no canvia en desplegar: el valor inicial és el de la constant.
- La constant `SAFETY_NET_GIVE_UP` passa a ser la clau de l'ajust, com `SAFETY_NET_AGE`, i desapareix la nota `shortcut:`.
- Allargar el termini deixa més temps en curs un intent que potser s'ha pagat; escurçar-lo no pot baixar de 24 hores, i per tant cap caiguda curta del proveïdor no envia un intent a revisar abans del reintent de l'endemà.
- La PR és `risc:alt` (pagaments, permisos, migracions) i la revisa el propietari.

## Fonts

- Instrucció escrita del propietari del 16/11/2026.
- [Addenda de la 055 del 05b](../planning.md#M05b-addenda-055) (VC-17, RN-M05b-24) i [P-102](pendents.md).
