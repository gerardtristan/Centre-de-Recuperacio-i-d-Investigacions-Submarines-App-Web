# 029 — «Compte personal» en lloc de «compte de soci»

- **Data:** 27/10/2026
- **Estat:** Acceptada

## Context
Les decisions 015 i 018 parlen de «compte de soci» (el compte que entra amb correu a l'àrea de socis). Però la decisió 021 permet que una persona no sòcia en tingui un de manera opcional, i llavors el nom confon el compte amb la relació de soci (mòdul 01).

## Decisió
- El compte que entra amb correu únic, verifica i recupera per correu i té el doble factor opcional es diu **compte personal**, a la interfície, als documents nous i al codi.
- «Soci» queda per a la relació de soci del mòdul 01.
- Les regles no canvien. Als documents anteriors (decisions 015 i 018, checklist C2, C4 i C5, arquitectura), «compte de soci» s'ha de llegir com «compte personal».

## Fonts
- Acceptació de la proposta Q-33 de la spec 00 comunicada per l'equip el 27/10/2026 (revisió del commit 8156443)
- [015](015-doble-factor-i-comptes-administrador.md), [018](018-perfil-comptes-i-rols.md), [021](021-persones-no-socies-com-a-convidades.md)
