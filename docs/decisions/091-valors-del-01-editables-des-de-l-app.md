# 091. Valors i tipus de soci del 01 editables des de l'app

- **Data:** 13/11/2026
- **Estat:** Acceptada (propietari, 13/11/2026; PR #28 aprovada). El contingut és la resposta escrita del propietari a la [P-79](pendents.md) (tauler, F-007): **opció A**.
- **Origen:** [revisió del codi](../estat/revisio-valors-configurables.md) de valors i llistes de negoci escrits al codi, i la regla de la PR #24 (valors i llistes de negoci són dades editables des de l'app; [055](055-ajustos-configurables-i-addendes.md) i [059](059-rols-i-permisos-editables.md)).

## Context

La revisió troba tres coses del mòdul 01 que no es poden canviar des de l'app:

1. El **termini del suplement** del canvi a ple dret (7 dies, RN-M01-76; confirmat per la [085](085-respostes-del-responsable-a-les-preguntes-pendents-de-t-m00-i-t-m01.md), T-1) és una constant del codi, i cap tasca no el porta als ajustos.
2. Els **recordatoris de quota** (−15, −1, 0, +15 i +30 dies; RN-M01-14 amb la precisió de la [072](072-respostes-del-responsable-a-la-ronda-1-de-pendents.md), Q-061) són en una variable d'entorn. La T-M01-32 els havia de portar als ajustos, però la clau de VC-02 («dies abans» i «dies després») no pot desar els cinc dies.
3. Els **tipus de soci** són dades, però les regles depenen de dos codis fixos (`supporter` i `full`): un tipus creat des de l'app no tindria cap regla, i no hi ha cap pantalla per crear-ne.

El 01 és congelat ([089](089-prova-d-acceleracio-interruptors-d1-a-d6.md), D1): una regla seva només es canvia amb una decisió numerada i una sola edició al lloc de la regla, en una PR `risc:alt`.

## Decisió

1. **VC-02 passa a ser una llista d'enters** (`members.fee_reminder_offsets`): dies respecte del venciment, amb el valor inicial que ja fa servir el codi. La variable d'entorn desapareix.
2. **El termini del suplement passa als ajustos** com a VC-53 (`members.type_change_supplement_due_days`), amb valor inicial 7. Els textos que diuen «una setmana» en llegeixen el valor.
3. **Les regles dels tipus de soci depenen d'atributs del tipus**, no del seu codi, i els tipus es poden crear, editar i desactivar des de la pantalla d'ajustos del 01. Els dos tipus actuals conserven exactament les regles que tenen avui.
4. Els punts 1 i 2 amplien la **T-M01-32**. El punt 3 és una tasca nova, la **T-M01-52**, que va després de la T-M01-32.

L'edició del pla és una sola: un bloc nou al final de l'[addenda de la 055 del 01](../planning.md#M01-addenda-055), amb els valors, les regles RN-M01-106 i RN-M01-107, els criteris CA-M01-123 a 125 i les dues tasques. On el bloc i l'[apèndix de valors configurables](../planning.md#valors-configurables) no coincideixen per a VC-02, val el bloc.

## Conseqüències

- Cap import no canvia: els valors inicials són els que el codi fa servir avui.
- El rang dels dos valors és una proposta (tipus configurable de la [089](089-prova-d-acceleracio-interruptors-d1-a-d6.md), D2); el tresorer el pot revisar sense cap decisió nova.
- Qui veu i qui edita la pantalla d'ajustos del 01 segueix el permís de dos nivells per apartat (resposta a la [P-75](pendents.md), RN-RP-22).
- Una pantalla que crea tipus de soci toca regles de quota i d'edat: la T-M01-52 és `risc:alt`.

## Fonts

- Resposta escrita del propietari del 13/11/2026 al tauler de preguntes (F-007 = A).
- [Revisió del codi](../estat/revisio-valors-configurables.md), punt 3.
