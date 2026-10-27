# 015 — Doble factor i comptes d'administrador separats

- **Data:** 27/10/2026
- **Estat:** Acceptada (resol P-05; substitueix [003](003-autenticacio-doble-factor.md)). L'abast exacte dels rols (P-17), la relació amb la checklist C4 i C5 (P-18) i el domini dels àlies (P-15) estan [A validar].

## Context
Els documents d'origen no coincidien en qui havia de fer servir el doble factor (vegeu 003). A més, si una mateixa persona és sòcia i, alhora, administradora, un sol compte amb recuperació per correu fa que qui controli el seu correu personal pugui controlar també l'administració.

## Alternatives
- Un sol compte per persona amb diversos rols (com suggereix funcionalitats §2): més senzill, però la recuperació per correu dona accés a l'administració.
- Dos comptes per a cada administrador: un de soci i un d'administrador, amb regles d'accés diferents.

## Decisió
1. **Doble factor (TOTP) obligatori** per a tots els rols amb accés a diners o a dades de socis, i per als comptes d'emergència.
2. **Dos comptes per a cada administrador, lligats a la mateixa persona:**

   | | Compte de soci | Compte d'administrador |
   |---|---|---|
   | Inici de sessió | Correu (únic) | Nom d'usuari (únic) |
   | Entrada | Àrea de socis | Entrada d'administració separada |
   | Correu | Únic; serveix per entrar i recuperar la contrasenya | No únic; només per a notificacions |
   | Recuperar la contrasenya | Per correu | **Mai per correu:** la restableix un altre administrador, o s'hi entra amb codis de recuperació guardats fora de línia |
   | Doble factor | Opcional | Obligatori |

3. **Comptes d'emergència** (com a mínim dos), amb doble factor i codis de recuperació fora de línia.
4. El **registre d'activitat** guarda quin compte (de soci o d'administrador) ha fet cada acció, a més de la persona.
5. [A validar] Més endavant, migrar el correu de notificació dels comptes d'administrador a àlies del domini del club, després de comprovar com està gestionat el domini (cris.es segons aquesta decisió; cris.barcelona segons el context: P-15) i el correu actual.

## Conseqüències
- La base comuna ha de modelar la persona amb un o més comptes d'accés; el permís depèn del compte, no només de la persona.
- Cal un procediment escrit per restablir la contrasenya d'un administrador i per fer servir els comptes d'emergència.
- Les regles C4 (restabliment per correu) i C5 (verificació de correu) de la checklist s'apliquen als comptes de soci; per als d'administrador cal una regla pròpia (P-18).
- Si només queda un administrador actiu i perd l'accés, l'única via són els codis de recuperació o els comptes d'emergència: s'han de custodiar en dos llocs.

## Fonts
- Resolució de P-05 comunicada per l'equip el 27/10/2026
- [003](003-autenticacio-doble-factor.md) i les fonts que cita
- `docs/checklist-produccio.md`, C2, C4 i C5
